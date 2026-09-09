interface Props {
  steps: string[];
  current: number;
  furthestReached: number;
  onSelect: (i: number) => void;
}

export default function Stepper({ steps, current, furthestReached, onSelect }: Props) {
  return (
    <div className="stepper">
      {steps.map((label, i) => (
        <button
          key={label}
          className={i === current ? "active" : i < current ? "done" : ""}
          disabled={i > furthestReached}
          onClick={() => onSelect(i)}
        >
          {i + 1}. {label}
        </button>
      ))}
    </div>
  );
}
