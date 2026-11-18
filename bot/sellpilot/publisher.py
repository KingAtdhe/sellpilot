"""Puts a package on sale in Polar: files -> download benefit -> product -> checkout link."""
from __future__ import annotations

from .polar import Polar


def publish(polar: Polar, pkg, currency: str = "usd", log=print) -> dict:
    file_ids = []
    for name, data in pkg.files.items():
        file_ids.append(polar.upload(name, data, "application/pdf", "downloadable"))
    log(f"  uploaded {len(file_ids)} PDFs")
    benefit = polar.create_benefit_files("PDF files: A4, US Letter, low-ink", file_ids,
                                         {"sp_slug": pkg.metadata["sp_slug"]})
    media = [polar.upload(n, d, "image/png", "product_media") for n, d in pkg.images + [pkg.pin]]
    log(f"  uploaded {len(media)} images")
    product = polar.create_product(pkg.name, pkg.description, pkg.price_cents, currency, media, pkg.metadata)
    polar.set_benefits(product["id"], [benefit["id"]])
    link = polar.checkout_link(product["id"], label=pkg.metadata["sp_slug"])
    md = dict(product.get("metadata") or pkg.metadata, sp_link=link["url"])
    product = polar.update_product(product["id"], metadata=md)
    log(f"  live: {pkg.name}  ({pkg.price_cents / 100:.2f} {currency.upper()})")
    return product


def publish_bundle(polar: Polar, name, description, price_cents, currency, benefit_ids, media_ids, metadata) -> dict:
    product = polar.create_product(name, description, price_cents, currency, media_ids, metadata)
    polar.set_benefits(product["id"], benefit_ids)
    link = polar.checkout_link(product["id"], label=metadata.get("sp_slug", ""))
    md = dict(product.get("metadata") or metadata, sp_link=link["url"])
    return polar.update_product(product["id"], metadata=md)
