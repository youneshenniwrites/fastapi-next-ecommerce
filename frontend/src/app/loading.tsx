export default function Loading() {
  return (
    <main id="main" className="loading">
      <div role="status" aria-label="Loading collection">
        <p className="eyebrow">A MOMENT OF SPACE</p>
        <h1>Gathering the collection…</h1>
        <div className="skeleton-grid">
          {[1, 2, 3].map((i) => (
            <div className="skeleton" key={i} />
          ))}
        </div>
      </div>
    </main>
  );
}
