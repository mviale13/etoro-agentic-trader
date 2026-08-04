type Props = {
  label: string;
  onClick: () => void;
};

export function ContinueButton({
  label,
  onClick,
}: Props) {
  return (
    <button
      onClick={onClick}
      className="rounded-xl bg-slate-900 px-8 py-4 text-lg font-medium text-white transition hover:bg-slate-800"
    >
      {label}
    </button>
  );
}
