type IconProps = { className?: string };

const base = 'h-5 w-5 shrink-0';

function Svg({ className, d }: IconProps & { d: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`${base} ${className ?? ''}`}
      aria-hidden
    >
      <path d={d} />
    </svg>
  );
}

export const IconDashboard = (p: IconProps) => (
  <Svg {...p} d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z" />
);
export const IconClipboard = (p: IconProps) => (
  <Svg {...p} d="M6 2h9l5 5v15H6zM14 2v5h5M9 12h6M9 16h6" />
);
export const IconScale = (p: IconProps) => (
  <Svg {...p} d="M12 3v3M5 21h14M12 6l-7 8h14l-7-8" />
);
export const IconFlask = (p: IconProps) => (
  <Svg {...p} d="M9 3h6M10 3v5l-5 9a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3" />
);
export const IconReport = (p: IconProps) => (
  <Svg {...p} d="M6 2h9l5 5v15H6zM14 2v5h5M9 15l2 2 4-4" />
);
export const IconUsers = (p: IconProps) => (
  <Svg {...p} d="M8 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM2 21v-1a6 6 0 0 1 12 0v1M16 3.5a3 3 0 0 1 0 6M22 21v-1a6 6 0 0 0-4-5.6" />
);
export const IconLogout = (p: IconProps) => (
  <Svg {...p} d="M15 17l5-5-5-5M20 12H9M12 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h6" />
);
export const IconKey = (p: IconProps) => (
  <Svg {...p} d="M21 2l-2 2m-7.6 7.6a5.5 5.5 0 1 1-7.8 7.8 5.5 5.5 0 0 1 7.8-7.8zm0 0L15 8m-4 4l2-2m4-4l2-2" />
);