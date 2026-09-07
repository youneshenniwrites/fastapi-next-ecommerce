import Link from "next/link";
export default function NotFound() {
  return (
    <main id="main" className="state">
      <p className="eyebrow">NOT FOUND</p>
      <h1>This object has moved on.</h1>
      <p>Explore the collection to find something else for your space.</p>
      <Link className="button" href="/#collection">
        Back to collection
      </Link>
    </main>
  );
}
