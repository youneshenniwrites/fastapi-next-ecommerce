import { describe, expect, it } from "vitest";
import {
  accountHref,
  accountIntent,
  collectionIntent,
  loginDestination,
  signInToAddHref,
} from "../src/lib/account-return";

const intent = (query: string) => accountIntent(new URLSearchParams(query));

describe("product return after sign-in", () => {
  it("keeps a product and the canonical collection filters", () => {
    expect(
      intent(
        "product=12&page=2&sort=price-asc&in_stock=1&q=%20lamp%20&category=lighting",
      ),
    ).toEqual({
      destination:
        "/products/12?category=lighting&q=lamp&in_stock=1&sort=price-asc&page=2",
      query:
        "?product=12&category=lighting&q=lamp&in_stock=1&sort=price-asc&page=2",
    });
    expect(signInToAddHref(12, "?q=lamp&category=lighting")).toBe(
      "/login?product=12&category=lighting&q=lamp",
    );
    expect(signInToAddHref(12, "category=lighting")).toBe(
      "/login?product=12&category=lighting",
    );
    expect(
      accountIntent({ product: "5", category: "lighting", next: "https://no" }),
    ).toEqual({
      destination: "/products/5?category=lighting",
      query: "?product=5&category=lighting",
    });
    expect(accountIntent({ product: ["5", "6"] })).toEqual(collectionIntent);
    expect(accountIntent({ product: undefined })).toEqual(collectionIntent);
    expect(accountIntent({})).toEqual(collectionIntent);
  });

  it("returns to the collection when no valid product is present", () => {
    expect(intent("")).toEqual(collectionIntent);
    expect(intent("category=lighting&q=lamp")).toEqual(collectionIntent);
    expect(signInToAddHref(Number.NaN)).toBe("/login");
    expect(accountHref("login", collectionIntent)).toBe("/login");
    expect(accountHref("register", collectionIntent)).toBe("/register");
  });

  it("rejects external, protocol-relative, malformed and oversized product ids", () => {
    for (const product of [
      "https://attacker.example",
      "//attacker.example",
      "/products/1",
      "../admin",
      "1e2",
      "01",
      "0",
      "-1",
      "1.5",
      "",
      " 1",
      "1 ",
      "2147483648",
      "9999999999",
      "9007199254740991",
      "javascript:alert(1)",
      "1\n2",
    ]) {
      expect(intent(`product=${encodeURIComponent(product)}`)).toEqual(
        collectionIntent,
      );
    }
    expect(intent("product=1&product=2")).toEqual(collectionIntent);
    expect(loginDestination("https://attacker.example/products/1")).toBe(
      "/#collection",
    );
    expect(loginDestination("//attacker.example/products/1")).toBe(
      "/#collection",
    );
    expect(loginDestination("/products/1#account")).toBe("/#collection");
    expect(loginDestination("http://[")).toBe("/#collection");
    expect(
      loginDestination("https://user:secret@vindor.local/products/1"),
    ).toBe("/#collection");
    expect(loginDestination("https://:secret@vindor.local/products/1")).toBe(
      "/#collection",
    );
    expect(signInToAddHref(0)).toBe("/login");
    expect(signInToAddHref(2147483648)).toBe("/login");
  });

  it("discards unrecognised parameters and never copies credentials", () => {
    expect(
      intent(
        "product=4&next=https://attacker.example&email=person@example.test&password=secret&token=abc",
      ),
    ).toEqual({
      destination: "/products/4",
      query: "?product=4",
    });
    expect(
      loginDestination(
        "/products/4?next=https://attacker.example&email=person@example.test",
      ),
    ).toBe("/products/4");
    expect(
      accountHref("login", {
        destination: "/products/4?next=https://attacker.example",
        query:
          "?product=4&next=https://attacker.example&email=person@example.test",
      }),
    ).toBe("/login");
  });

  it("drops invalid collection filters and keeps the product", () => {
    expect(intent("product=8&sort=nope&page=0&q=a&q=b")).toEqual({
      destination: "/products/8",
      query: "?product=8",
    });
    expect(intent("product=8&category=lighting&in_stock=1")).toEqual({
      destination: "/products/8?category=lighting&in_stock=1",
      query: "?product=8&category=lighting&in_stock=1",
    });
  });

  it("builds login and register links only from a canonical intent", () => {
    const kept = intent("product=3&category=lighting");
    expect(accountHref("register", kept)).toBe(
      "/register?product=3&category=lighting",
    );
    expect(accountHref("login", kept)).toBe(
      "/login?product=3&category=lighting",
    );
    expect(loginDestination(kept.destination)).toBe(kept.destination);
    expect(loginDestination("/#collection")).toBe("/#collection");
    expect(
      accountHref("login", { destination: "/products/3", query: "product=3" }),
    ).toBe("/login");
  });
});
