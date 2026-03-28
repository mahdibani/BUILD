export default function PageTransition({ children, className = "", style }) {
  return (
    <div className={`page-transition ${className}`.trim()} style={style}>
      {children}
    </div>
  );
}
