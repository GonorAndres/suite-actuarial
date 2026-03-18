# Portfolio Site Update Instructions

## 1. Update the project card in `src/data/projects.ts`

Find the existing `actuarial-suite` entry and add/update these fields:

```typescript
{
    slug: 'actuarial-suite',
    title: {
        es: 'Suite Actuarial Mexicana',
        en: 'Mexican Actuarial Suite',
    },
    description: {
        es: 'Libreria Python con 6 fases: tablas EMSSA-09, primas de vida (temporal, ordinario, dotal), reaseguro (QS, XoL, SL), reservas (Chain Ladder, BF, Bootstrap), RCS bajo LISF, reportes CNSF y validaciones SAT. 307 tests, 87% cobertura, dashboard Streamlit.',
        en: 'Python library with 6 phases: EMSSA-09 mortality tables, life premiums (term, whole, endowment), reinsurance (QS, XoL, SL), reserves (Chain Ladder, BF, Bootstrap), RCS under LISF, CNSF reports and SAT tax validations. 307 tests, 87% coverage, Streamlit dashboard.',
    },
    // ADD: link to live demo once deployed
    url: '<STREAMLIT_CLOUD_URL>',
    repo: 'https://github.com/GonorAndres/Analisis_Seguros_Mexico',
    platform: 'Streamlit',
    category: 'actuarial',
    tags: ['Python', 'Pydantic', 'Streamlit', 'LISF', 'RCS', 'EMSSA-09', 'Chain Ladder'],
    variant: 'wide',
    screenshot: '/screenshots/actuarial-suite.png',
    // ADD: link to blog post
    blogSlug: 'suite-actuarial',
    relatedTo: ['sima', 'life-insurance', 'property-insurance'],
}
```

## 2. Add blog post files

Copy:
- `docs/portfolio/blog-es.md` -> `src/content/blog/es/suite-actuarial.md`
- `docs/portfolio/blog-en.md` -> `src/content/blog/en/suite-actuarial.md`

## 3. Add screenshot

Capture the Streamlit dashboard home page and save as:
- `public/screenshots/actuarial-suite.png`

## 4. Deploy Streamlit to Streamlit Community Cloud

1. Go to https://share.streamlit.io
2. Connect repo: GonorAndres/Analisis_Seguros_Mexico
3. Main file path: streamlit_app/Home.py
4. Python version: 3.11
5. The root `requirements.txt` will be auto-detected
