# Kerala taxi packages site

A static site built with Python (Jinja2 + PyYAML). There is no server or database, and it is free to host.

## Edit content
- `site.yaml`: business name, phone, WhatsApp number, address, domain, inclusions, vehicles
- `packages.yaml`: one entry per package (prices per vehicle, highlights, optional image)
- Images: drop files in `static/images/` and add `image: munnar.jpg` to the package. Use WebP or compressed JPG, about 1200px wide.

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python build.py --serve      # open http://localhost:8000
```
The build stops with a clear message if a package uses an unknown vehicle or a missing image.

## Deploy to Cloudflare Pages (free)
1. Push this folder to a GitHub repo. `dist/` is git-ignored.
2. Cloudflare dashboard > Workers & Pages > Create > Pages > Connect to Git, then pick the repo.
3. Build command: `pip install -r requirements.txt && python build.py`
   Build output directory: `dist`
4. After the first deploy, open Custom domains and add the client's domain.
5. Set `url:` in `site.yaml` to that domain so the sitemap and canonical links are right.

To update prices, edit `packages.yaml`, then `git push`. The site redeploys in about a minute.

## After launch
- Submit `https://yourdomain/sitemap.xml` in Google Search Console.
- Create a Google Business Profile for the client and add the website link.
- Turn on Cloudflare Web Analytics, which is free and cookie-less.
