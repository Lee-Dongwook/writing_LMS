import logging

from fastapi import APIRouter, Depends, status, Request, HTTPException
from pydantic import TypeAdapter, ValidationError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/doc", tags=["doc"])

@router.post(
    "/{doc_uuid}/dynamic_submit",
    summary="Submit data to a dynamic form based doc's style",
    status_code=status.HTTP_200_OK
)
async def submit_dynamic_form_endpoint(
    doc_uuid: str,
    request: Request,
    payload: dict = Depends(get_request_payload),
    user: UserRead = Depends(verify_token),
    db: AsyncSession = Depends(get_async_db),
    thread_uuid: str | None = Query(None, alias="thread_uuid"),
) -> Response:
    document = await get_doc_by_uuid(doc_uuid, user.uuid, db)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    try:
        validation_model = create_dynamic_model_from_elements(
            f"DynamicFormModel_{doc_uuid}", doc.inputs,
        )

        if thread_uuid:
            allowed_keys = set(validation_model.model_fields.keys())
            validated_data = {}

            errors = []
            for k, v in payload.items():
                if k in allowed_keys:
                    try:
                        field_info = validation_model.model_fields[k]
                        adapter = TypeAdapter(field_info.annotation)
                        validated_value = adapter.validate_python(v)
                        validated_data[k] = validated_value
                    except ValidationError as e:
                        errors.extend([{"loc": [k, *err.get('loc',())], "msg": err['msg'], "type": err['type']} for err in e.errors()])
            if errors:
                raise HTTPException(status_code=422, detail=errors)
        else:
            validated_data = validation_model.model_validate(payload)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors()) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create dynamic model: {e}",
        ) from e

    final_payload = {}
    if thread_uuid:
        final_payload = validated_data
    else:
        try:
            final_payload = await process_and_validate_files_from_payload(
                payload=validated_data,
                elements=doc.inputs,
                user_uuid=str(user.uuid),
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                 status_code=500, detail=f"An error occurred during file processing: {e}",
            ) from e

    pipeline = doc.pipeline
    if not thread_uuid and not pipeline:
        return {"status": "success", "processed_data": final_payload}

    streaming = False
    accept_header = request.headers.get("accept", "application/json")

    if "text/event-stream" in accept_header:
        streaming = True

    async def _run_in_context():
        async with get_checkpoint() as cp:
            pipeline_response = run_pipeline(
                unique=doc.uuid,
                pipeline=pipeline,
                payload=final_payload,
                user_uuid=user.uuid,
                thread_uuid=thread_uuid,
                streaming=streaming,
                checkpointer=cp,
            )

            if streaming:
                async for chunk in _stream_wrapper(pipeline_response):
                    yield chunk
            else:
                # For non-streaming, we need to consume the generator to get the final result
                final_res = {}
                async for res in pipeline_response:
                    final_res = res
                yield final_res
    if streaming:
        return StreamingResponse(
            content=_run_in_context(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control",
            },
        )
    else:
        final_res = {}
        async for chunk in _run_in_context():
            final_res = chunk

        # Check if the pipeline execution resulted in an error
        if final_res.get("status") == "pipeline_failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=final_res,
            )
    return final_res

