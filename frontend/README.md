# Writing LMS — Frontend (Mockup)

`dashboard.png` / `people.png` 디자인 구도를 기반으로 한 프론트엔드 가안(목업).

## 스택

- React 18 + Vite 6 + TypeScript
- Tailwind CSS 3
- Zustand (사이드바/모달 등 UI 상태)
- TanStack Query (mock API 데이터 페칭 — `src/api/mock.ts`)

## 실행

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
```

빌드/타입체크: `npm run build`

## 구조

```
src/
  api/         # mock.ts (지연 시뮬레이션) + hooks.ts (useQuery 래퍼)
  store/       # uiStore.ts (Zustand)
  components/
    layout/    # Sidebar, Header, AppLayout
    dashboard/ # WelcomeCard, ProgressCard, NoticeCard, Calendar, ScheduleList
    OnlineUsersModal / OnlineUsersButton   # people.png 접속자 리스트
  pages/       # Dashboard.tsx
```

> 데이터는 전부 목업(`src/api/mock.ts`)입니다. 추후 FastAPI(`:8000`) 연동 시
> `mock.ts`의 함수만 실제 `fetch`로 교체하면 됩니다.
