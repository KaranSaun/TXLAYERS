# TexLayerAI

**AI-Powered Textile Design Automation System**

TexLayerAI is a production-grade web application that automates textile design processing using state-of-the-art AI models. Upload any design image and automatically get print-ready layered files with AI-generated colorway variants.

## Features

- **AI Upscaling**: Real-ESRGAN upscales designs to 300 DPI print quality
- **Smart Segmentation**: SAM2 and rembg separate motifs from backgrounds with precision
- **Color Clustering**: Delta-E CIE2000 color science groups similar colors into layers (max 50)
- **Edge Cleanup**: OpenCV morphological operations for clean, professional edges
- **Layer Export**: Multi-layer TIFF files ready for print production
- **Colorway Generation**: Automatically creates 10 design variants with different color schemes
- **Modern UI**: Clean Next.js interface for upload, preview, and download

## Tech Stack

### Backend
- **Framework**: FastAPI + Uvicorn
- **Database**: PostgreSQL + SQLAlchemy + Alembic
- **Job Queue**: Celery + Redis
- **Storage**: MinIO (S3-compatible)
- **AI Models**: Real-ESRGAN, SAM2, rembg
- **Image Processing**: OpenCV, Pillow, scikit-image

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Styling**: TailwindCSS + shadcn/ui
- **State**: Zustand
- **Icons**: Lucide React

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Reverse Proxy**: Nginx

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- At least 8GB RAM (16GB recommended for AI models)
- 10GB free disk space

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd texlayer-ai
```

2. **Download AI models**
```bash
cd backend
chmod +x download_models.sh
./download_models.sh
cd ..
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env and set JWT_SECRET_KEY to a secure random string
```

4. **Start the system**
```bash
docker-compose up --build
```

5. **Initialize database**
```bash
# In a new terminal
docker-compose exec backend alembic upgrade head
```

6. **Access the application**
- Frontend: http://localhost
- Backend API: http://localhost/api
- MinIO Console: http://localhost:9001

## Architecture

```
┌─────────────┐
│   Nginx     │ :80 (Reverse Proxy)
└──────┬──────┘
       │
       ├─────────────────┐
       │                 │
┌──────▼──────┐   ┌──────▼──────┐
│  Next.js    │   │   FastAPI   │ :8000
│  Frontend   │   │   Backend   │
└─────────────┘   └──────┬──────┘
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
│  PostgreSQL │   │    Redis    │   │    MinIO    │
│  Database   │   │   Broker    │   │   Storage   │
└─────────────┘   └──────┬──────┘   └─────────────┘
                         │
                  ┌──────▼──────┐
                  │   Celery    │
                  │   Worker    │
                  └─────────────┘
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Create new user account
- `POST /api/auth/login` - Login and get JWT token

### Designs
- `POST /api/designs/upload` - Upload design file (multipart/form-data)
- `GET /api/designs` - List all user designs
- `GET /api/designs/{id}` - Get design details with layers
- `DELETE /api/designs/{id}` - Delete design

### Jobs
- `GET /api/jobs/{id}` - Get job status
- `GET /api/jobs/{id}/progress` - Get job progress percentage
- `GET /api/jobs/{id}/stream` - Server-Sent Events for real-time updates

### Colorways
- `GET /api/colorways/designs/{id}/colorways` - List colorways for design
- `POST /api/colorways/designs/{id}/colorways/generate` - Generate colorways
- `POST /api/colorways/designs/{id}/colorways/manual` - Create custom colorway

### Downloads
- `GET /api/download/designs/{id}/tif` - Download master TIFF
- `GET /api/download/colorways/{id}/tif` - Download colorway TIFF
- `GET /api/download/designs/{id}/bundle` - Download all colorways as ZIP

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://texlayer:texlayer_pass@postgres:5432/texlayer_db` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `MINIO_ENDPOINT` | MinIO server endpoint | `minio:9000` |
| `MINIO_ACCESS_KEY` | MinIO access key | `minioadmin` |
| `MINIO_SECRET_KEY` | MinIO secret key | `minioadmin` |
| `JWT_SECRET_KEY` | JWT signing secret | **CHANGE IN PRODUCTION** |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `JWT_EXPIRY_HOURS` | Token expiry time | `24` |
| `DELTA_E_MERGE_THRESHOLD` | Color similarity threshold | `0.4` |
| `MAX_LAYERS` | Maximum layers per design | `50` |
| `MAX_COLORWAYS` | Maximum colorway variants | `10` |
| `MODEL_PATH` | AI models directory | `/app/models_cache` |
| `CELERY_CONCURRENCY` | Worker concurrency | `2` |

## Development Mode

### Backend Only
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
./download_models.sh
uvicorn app.main:app --reload
```

### Frontend Only
```bash
cd frontend
npm install
npm run dev
```

### Celery Worker
```bash
cd backend
celery -A app.workers.celery_app worker --loglevel=info
```

## Processing Pipeline

1. **Upload** - User uploads design file (JPG, PNG, TIFF, PDF, PSD)
2. **Upscale** - Real-ESRGAN upscales to 300 DPI
3. **Segment** - SAM2/rembg separates motifs from background
4. **Cluster** - KMeans + Delta-E groups similar colors
5. **Build** - Creates individual layer masks
6. **Export** - Generates multi-layer TIFF file
7. **Colorways** - Creates 10 recolored variants

## Colorway Generation Strategies

1. **Hue Shift** (3 variants): +30°, +60°, +90° hue rotation on motifs
2. **Background Swap** (2 variants): Ivory and Charcoal backgrounds
3. **Seasonal** (2 variants): Earth Tones and Pastels
4. **Complementary** (1 variant): 180° hue shift
5. **Monochromatic** (1 variant): Same hue, different lightness
6. **Custom** (1 variant): Navy background + 45° motif shift

## Troubleshooting

### Models not downloading
```bash
cd backend
chmod +x download_models.sh
./download_models.sh
```

### Database connection errors
```bash
docker-compose down
docker-compose up -d postgres
docker-compose exec backend alembic upgrade head
docker-compose up
```

### Out of memory errors
- Increase Docker memory limit to 8GB+
- Reduce `CELERY_CONCURRENCY` to 1
- Process smaller images

### Frontend TypeScript errors
All TypeScript errors are expected before running `npm install` in the frontend directory. They will resolve automatically once dependencies are installed.

## Production Deployment

1. **Security**:
   - Change `JWT_SECRET_KEY` to a strong random value
   - Update MinIO credentials
   - Enable HTTPS with SSL certificates
   - Set `ALLOWED_ORIGINS` to your domain

2. **Performance**:
   - Use production-grade PostgreSQL instance
   - Configure Redis persistence
   - Set up MinIO with proper storage backend
   - Increase Celery worker concurrency based on CPU cores

3. **Monitoring**:
   - Add logging aggregation (ELK stack)
   - Set up health check endpoints
   - Monitor Celery queue length
   - Track storage usage

## License

Proprietary - All rights reserved

## Support

For issues and questions, please contact the development team.

---

**Built with ❤️ for textile designers worldwide**
