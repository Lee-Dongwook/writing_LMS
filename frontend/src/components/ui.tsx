import type { ButtonHTMLAttributes, ReactNode } from "react";

// 에디토리얼 공용 프리미티브
// 원칙: 그림자·회색 보더 최소화, 면(surface)과 여백으로 구분, 색은 진홍·먹으로만.

// 섹션 위 작은 라벨 (14px/700 진홍)
export function Eyebrow({ children }: { children: ReactNode }) {
  return (
    <div className="text-[13px] font-bold uppercase tracking-wide text-brand-600">
      {children}
    </div>
  );
}

// 중립면 카드 — 기본 그림자 없음, 호버 시 살짝 떠오름(선택)
export function Card({
  children,
  className = "",
  hover = false,
}: {
  children: ReactNode;
  className?: string;
  hover?: boolean;
}) {
  return (
    <div
      className={`rounded-card bg-surface p-6 transition-all duration-200 ${
        hover ? "hover:-translate-y-0.5 hover:shadow-lift" : ""
      } ${className}`}
    >
      {children}
    </div>
  );
}

// 통계 블록 — 큰 숫자(타입 위계)로 정보 표현
export function Stat({
  label,
  value,
  unit,
  sub,
  accent = false,
}: {
  label: string;
  value: string | number;
  unit?: string;
  sub?: ReactNode;
  accent?: boolean;
}) {
  return (
    <div>
      <div className="text-sm text-slate-500">{label}</div>
      <div className="mt-1.5 flex items-baseline gap-1">
        <span
          className={`stat-num text-[40px] font-extrabold leading-none ${
            accent ? "text-brand-600" : "text-ink"
          }`}
        >
          {value}
        </span>
        {unit && (
          <span className="text-base font-semibold text-slate-400">{unit}</span>
        )}
      </div>
      {sub && <div className="mt-1.5 text-xs text-slate-400">{sub}</div>}
    </div>
  );
}

type BtnProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost";
};

// pill 버튼 — primary: 먹색 / ghost: 흰 배경 라인
export function PillButton({
  variant = "primary",
  className = "",
  children,
  ...rest
}: BtnProps) {
  const styles =
    variant === "primary"
      ? "bg-ink text-white hover:bg-ink-soft"
      : "bg-white text-ink ring-1 ring-line hover:bg-surface";
  return (
    <button
      className={`inline-flex h-[46px] items-center justify-center rounded-full px-5 text-sm font-semibold transition-colors ${styles} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}

// 진행 막대 — 진홍 계열로 확실히 보이게, 위계는 농담(진하기)으로.
// strong: 강조/취약  ·  mid: 일반 데이터  ·  soft: 보조
type BarTone = 'strong' | 'mid' | 'soft'
const BAR_FILL: Record<BarTone, string> = {
  strong: 'bg-brand-600',
  mid: 'bg-brand-500',
  soft: 'bg-brand-300',
}
export function Bar({ pct, tone = 'mid' }: { pct: number; tone?: BarTone }) {
  return (
    <div className="h-2.5 w-full overflow-hidden rounded-full bg-brand-100">
      <div
        className={`h-full rounded-full ${BAR_FILL[tone]}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}
