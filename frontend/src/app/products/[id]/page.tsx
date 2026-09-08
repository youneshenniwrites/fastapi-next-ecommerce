import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { apiClient } from "@/lib/api/client";
import { money, productArt } from "@/lib/catalog";
export const dynamic = "force-dynamic";
export default async function ProductPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  if (!/^\d+$/.test(id) || !Number.isSafeInteger(Number(id)) || Number(id) < 1)
    notFound();
  const { data, response } = await apiClient().GET(
    "/api/v1/products/{product_id}",
    { params: { path: { product_id: Number(id) } } },
  );
  if (response.status === 404) notFound();
  if (!data || !response.ok) throw new Error("Product unavailable");
  return (
    <main id="main" className="detail">
      <Link className="back" href="/#collection">
        ← Back to the collection
      </Link>
      <div className="detail-grid">
        <div className="detail-art">
          <Image
            src={productArt(data.name)}
            alt={`Illustration of ${data.name}`}
            width={900}
            height={750}
            priority
          />
        </div>
        <div className="detail-copy">
          <p className="eyebrow">THE WORKSPACE COLLECTION</p>
          <h1>{data.name}</h1>
          <p className="detail-price">
            {money(data.price)} <span>GBP</span>
          </p>
          <p>{data.description}</p>
          <p className="availability">
            <span className={data.stock ? "dot" : "dot unavailable"} />
            {data.stock ? "In stock" : "Out of stock"}
          </p>
          <div className="demo-notice">
            <strong>A collection to explore.</strong>
            <p>
              This is a portfolio demonstration. Cart and checkout are coming
              next; no purchases can be made.
            </p>
          </div>
          <dl>
            <div>
              <dt>Collection</dt>
              <dd>Everyday focus</dd>
            </div>
            <div>
              <dt>Reference</dt>
              <dd>FORME / {String(data.id).padStart(3, "0")}</dd>
            </div>
          </dl>
        </div>
      </div>
    </main>
  );
}
