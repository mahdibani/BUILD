export default function MaterialIcon({
  name,
  className = "",
  filled = false,
  weight = 400,
}) {
  return (
    <span
      aria-hidden="true"
      className={`material-symbols-outlined ${className}`.trim()}
      style={{
        fontVariationSettings: `'FILL' ${filled ? 1 : 0}, 'wght' ${weight}, 'GRAD' 0, 'opsz' 24`,
      }}
    >
      {name}
    </span>
  );
}
