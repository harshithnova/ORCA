# ORCA Frontend

React + Vite + TypeScript + Leaflet frontend for the ORCA marine ecosystem reasoning system.

## Overview

The ORCA frontend provides:

- **Query Interface**: Natural language input for fishing zone queries
- **Interactive Map**: Leaflet-based map with candidate zone visualization
- **Risk/Suitability Cards**: Score display with progress indicators
- **Evidence Display**: Supporting data with source and validity information
- **Responsive Design**: Mobile-friendly UI using Tailwind CSS

## Architecture

```
src/
├── components/          # React components
│   ├── QueryInput.tsx      # Query input form
│   ├── Map.tsx             # Leaflet map visualization
│   ├── RecommendationCard.tsx  # Score and status display
│   ├── EvidenceDisplay.tsx     # Supporting evidence
│   ├── CandidateZonesPanel.tsx # Alternative zones
│   └── index.ts            # Component exports
├── services/            # API communication
│   └── api.ts              # ORCA API client
├── types/               # TypeScript types
│   └── index.ts            # Type definitions (matches API_CONTRACT.md)
├── utils/               # Utility functions
│   └── scoring.ts          # Score calculations and colors
├── styles/              # CSS styles
│   └── index.css           # Tailwind + custom styles
├── App.tsx              # Main app component
└── main.tsx             # Entry point
```

## Features

### 1. Query Input (`QueryInput.tsx`)
- Natural language query submission
- Example suggestions
- Error display
- Loading state

### 2. Interactive Map (`Map.tsx`)
- Leaflet with OpenStreetMap tiles
- Candidate zone markers
- Recommended zone highlighting
- Popup information on click
- Marker selection integration

### 3. Recommendation Card (`RecommendationCard.tsx`)
- **Suitability Score** (0-100): POOR → EXCELLENT
- **Risk Score** (0-100): LOW → SEVERE  
- **Confidence Score** (0-1): Data support quality
- **Status**: SAFE, CAUTION, BLOCK, or NO_SAFE_RECOMMENDATION
- Progress bars with color-coded levels
- Recommendation reasoning

### 4. Evidence Display (`EvidenceDisplay.tsx`)
- Supporting data with source attribution
- Parameter, value, unit, and validity period
- Data mode (CACHED_OFFICIAL vs SIMULATED_MVP)
- Data type (OBSERVATION, FORECAST, WARNING, REFERENCE)
- Source URLs and links

### 5. Candidate Zones (`CandidateZonesPanel.tsx`)
- List of alternative zones
- Individual scores for each zone
- Zone selection integration
- Status indicators

## Data Structure

### Types (defined in `src/types/index.ts`)

Matches the API contract from `API_CONTRACT.md`:

```typescript
interface ReasonResponse {
  status: StatusType;           // SAFE | CAUTION | BLOCK | NO_SAFE_RECOMMENDATION
  query: string;
  location: Location;
  requested_time: TimeWindow;
  recommendation: Recommendation;
  evidence: Evidence[];
  map: MapData;
}

interface Recommendation {
  zone_id: string;
  suitability_score: number;    // 0-100
  risk_score: number;           // 0-100
  confidence_score: number;     // 0-1
  reason: string;
}
```

## Setup

### Prerequisites
- Node.js 16+
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Update the API base URL:
```
VITE_API_BASE_URL=http://localhost:8000/api
```

### Development

```bash
npm run dev
```

Opens at `http://localhost:5173`

### Build

```bash
npm run build
```

Outputs to `dist/`

### Type Checking

```bash
npm run type-check
```

### Linting

```bash
npm run lint
```

## Integration

### Backend API

The frontend connects to a FastAPI backend at the `/api/v1/reason` endpoint.

**Request:**
```json
{
  "query": "Find a suitable and safe fishing zone near Kochi tomorrow morning."
}
```

**Response:**
Matches `API_CONTRACT.md` response format.

### Mock Data for Development

If the backend is not yet available, temporary mock responses can be added to `src/services/api.ts` for testing the UI.

## Styling

Uses **Tailwind CSS** with custom extensions:

- **Colors**: Ocean theme with safety indicators
- **Components**: Cards, badges, progress bars
- **Animations**: Smooth transitions and pulse effects
- **Responsive**: Mobile-first design

## Component Communication

```
App
├── QueryInput
│   └── onSubmit → orcaApi.reason()
├── Map
│   ├── receives: response, candidates
│   └── onZoneSelect → setSelectedZoneId
├── RecommendationCard
│   └── receives: response
├── CandidateZonesPanel
│   ├── receives: candidates, selectedZoneId
│   └── onZoneSelect → setSelectedZoneId
└── EvidenceDisplay
    └── receives: response
```

## Performance

- Code splitting via Vite
- Tree shaking for unused code
- Lazy loading of components (can be added)
- Efficient re-renders with React.memo
- Leaflet markers pooled and reused

## Accessibility

- Semantic HTML structure
- ARIA labels on interactive elements
- Keyboard navigation support
- Color contrast compliance
- Focus indicators

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Development Workflow

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes in `src/`
3. Type check: `npm run type-check`
4. Lint: `npm run lint`
5. Test locally: `npm run dev`
6. Build: `npm run build`
7. Commit and push to GitHub

## File Structure Summary

| File | Purpose |
|------|---------|
| `src/App.tsx` | Main app, state management |
| `src/main.tsx` | React entry point |
| `src/components/` | Reusable React components |
| `src/services/api.ts` | Backend API client |
| `src/types/index.ts` | TypeScript interfaces |
| `src/utils/scoring.ts` | Score calculations |
| `src/styles/index.css` | Tailwind + custom CSS |
| `vite.config.ts` | Vite build config |
| `tsconfig.json` | TypeScript config |
| `tailwind.config.js` | Tailwind theme config |
| `postcss.config.js` | PostCSS plugins |
| `index.html` | HTML entry point |
| `package.json` | Dependencies and scripts |

## Troubleshooting

### Port Already in Use
```bash
npm run dev -- --port 3000
```

### Module Not Found
- Check import paths use `@/` prefix
- Run `npm install` again
- Clear `node_modules` and reinstall

### Map Not Rendering
- Ensure Leaflet CSS is loaded in `index.html`
- Check browser console for errors
- Verify `react-leaflet` is installed

### API Errors
- Check backend is running at configured URL
- Verify API response format matches types
- Check browser console network tab

## Future Enhancements

- [ ] Real-time data updates via WebSocket
- [ ] Advanced filtering for zones
- [ ] Route optimization (post-MVP)
- [ ] Historical data comparison
- [ ] Export recommendations as PDF
- [ ] Multi-language support
- [ ] Offline mode

## License

Part of the ORCA project (SIH 2026 - SIH26176)

## Contributors

- Frontend + Map Team

## Related Documentation

- [API_CONTRACT.md](../API_CONTRACT.md)
- [DATA_CONTRACT.md](../DATA_CONTRACT.md)
- [ARCHITECTURE.md](../ARCHITECTURE.md)
- [MVP_SCOPE.md](../MVP_SCOPE.md)
