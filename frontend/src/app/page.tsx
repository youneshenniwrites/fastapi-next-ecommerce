import { RetryCatalog } from "@/components/retry-catalog";
import Image from "next/image";
import { apiClient } from "@/lib/api/client";
import { Catalog } from "@/components/catalog";
export const dynamic = "force-dynamic";
export default async function Home() {
  let products;
  try {
    const result = await apiClient().GET("/api/v1/products/", {
      params: { query: { limit: 100, skip: 0 } },
    });
    if (result.error || !result.data) throw new Error("Catalog unavailable");
    products = result.data;
  } catch {
    products = null;
  }
  return (
    <main id="main">
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">THE ART OF WORKING WELL</p>
          <h1>
            Room to think.
            <br />
            <em>Space to create.</em>
          </h1>
          <p className="intro">
            Thoughtful objects for the place you do your best work. Simple
            forms. A calmer everyday.
          </p>
          <a className="button" href="#collection">
            Explore the collection <span aria-hidden="true">↗</span>
          </a>
          <div className="hero-note">
            <span className="small-line" /> A considered workspace starts with
            less.
          </div>
        </div>
        <div className="hero-image">
          <Image
            src="/art/workspace.svg"
            alt="Illustration of a warm workspace with an oak monitor stand, task light and stationery"
            width={900}
            height={780}
            priority
          />
          <div className="image-caption">
            <span>THE EVERYDAY EDIT</span>
            <span>01 / 06</span>
          </div>
        </div>
      </section>
      <section id="collection" className="collection">
        <div className="section-heading">
          <div>
            <p className="eyebrow">LESS, BUT BETTER</p>
            <h2>Find your focus.</h2>
          </div>
          <p>Small details. A different kind of day.</p>
        </div>
        {products === null ? (
          <div className="state" role="alert" aria-label="Catalog unavailable">
            <h3>The collection is taking a moment.</h3>
            <p>We couldn’t reach the catalog. Please try again shortly.</p>
            <RetryCatalog />
          </div>
        ) : (
          <Catalog products={products} />
        )}
      </section>
      <section id="approach" className="approach">
        <p className="eyebrow">OUR APPROACH</p>
        <h2>
          A place for everything.
          <br />
          <em>More space for you.</em>
        </h2>
        <p>
          FORME explores a simple idea: a workspace should make room for your
          attention. This fictional collection brings warm textures and useful
          forms into everyday focus.
        </p>
        <span className="approach-mark" aria-hidden="true">
          f.
        </span>
      </section>
    </main>
  );
}
