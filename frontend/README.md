# Iran News Wire - Frontend

A clutter-free news UI for displaying fact-checked articles from the Iran News Wire pipeline.

## Tech Stack

- **Next.js 14** (App Router)
- **Tailwind CSS** for styling
- **Lucide React** for icons
- **date-fns** for date formatting

## Setup

### 1. Install dependencies

```bash
cd frontend
npm install
```

### 2. Configure environment

Copy the example environment file:

```bash
cp .env.local.example .env.local
```

The default configuration connects to the API at `http://localhost:8000`.

### 3. Start the API server

In a separate terminal, start the FastAPI backend:

```bash
# From the project root
pip install fastapi uvicorn
python -m src.api.server
```

### 4. Start the frontend

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the UI.

## Features

- **Article Feed**: Browse all processed articles with pagination
- **Filtering**: Filter by verification status (Verified/Unverified/Propaganda) and source type (Telegram/Web)
- **Search**: Full-text search across articles
- **Status Badges**: Visual indicators for fact-check status
- **Bias Score**: Visual representation of content bias (1-10 scale)
- **Fact-Check Notes**: Expandable section showing verification details
- **Translation Toggle**: View literal translation vs. edited copy

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx        # Root layout with header/footer
│   ├── page.tsx          # Home page (article feed)
│   ├── loading.tsx       # Loading skeleton
│   ├── not-found.tsx     # 404 page
│   └── article/[id]/
│       └── page.tsx      # Article detail page
├── components/
│   ├── ArticleCard.tsx   # Article preview card
│   ├── ArticleDetail.tsx # Full article view
│   ├── FilterBar.tsx     # Search and filters
│   ├── Pagination.tsx    # Page navigation
│   └── StatusBadge.tsx   # Status indicator badges
├── lib/
│   └── api.ts            # API client functions
└── package.json
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## API Endpoints

The frontend expects these API endpoints:

- `GET /api/articles` - List articles (with pagination, filtering, search)
- `GET /api/articles/{id}` - Get single article
- `GET /api/stats` - Get dashboard statistics
