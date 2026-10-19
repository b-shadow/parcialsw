import { expect, test } from "@playwright/test";

test("el shell de produccion queda disponible despues de perder conectividad", async ({ context, page }) => {
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: /bienvenido/i })).toBeVisible();

  const manifest = await page.request.get("/manifest.webmanifest");
  expect(manifest.ok()).toBe(true);
  expect(await manifest.json()).toMatchObject({
    name: "CASE Inteligente",
    display: "standalone",
    start_url: "/",
  });

  await page.evaluate(async () => {
    const registration = await navigator.serviceWorker.ready;
    if (!registration.active) throw new Error("Service worker sin activar");
  });
  await page.reload();
  await context.setOffline(true);
  await page.reload({ waitUntil: "domcontentloaded" });

  await expect(page.getByRole("heading", { name: /bienvenido/i })).toBeVisible();
});
