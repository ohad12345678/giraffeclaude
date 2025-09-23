# 🦒 Giraffe Quality Management System

A comprehensive, production-ready quality management system for the Giraffe restaurant chain, featuring a modern React frontend and FastAPI backend with Claude AI integration.

## 🚀 Features

### ✨ Core Functionality
- **Digital Quality Checks** - Intuitive forms for documenting food quality inspections
- **Comprehensive Scoring** - Multi-dimensional scoring system (taste, appearance, temperature, etc.)
- **Real-time Dashboard** - Interactive KPIs and performance metrics
- **AI-Powered Insights** - Claude AI analysis with Hebrew language support
- **Branch Management** - Multi-location support with role-based access

### 🎯 Advanced Features
- **Role-Based Permissions** - Admin, Manager, Branch Manager, and Viewer roles
- **Multi-language Support** - Full RTL support for Hebrew and Arabic
- **Mobile Responsive** - Works seamlessly on all devices
- **Export Capabilities** - CSV, XLSX, and PDF report generation
- **Image Upload** - Visual documentation of quality checks
- **Real-time Alerts** - Automatic notifications for low scores

### 🤖 AI Integration
- **Trend Analysis** - Automatic identification of quality patterns
- **Custom Questions** - Ask Claude specific questions about your data
- **Weekly Reports** - Auto-generated comprehensive reports in Hebrew
- **Anomaly Detection** - Early warning system for quality issues

## 🏗️ Architecture

### Backend (FastAPI)
```
backend/
├── app/
│   ├── api/v1/          # API endpoints
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic layer
│   └── utils/           # Configuration and utilities
```

### Frontend (React + TypeScript)
```
frontend/
├── src/
│   ├── components/      # Reusable UI components
│   ├── pages/          # Main application pages
│   ├── hooks/          # Custom React hooks
│   ├── services/       # API integration
│   └── types/          # TypeScript definitions
```

## 🚀 Quick Start

### Prerequisites
- **Node.js 18+** - [Download here](https://nodejs.org)
- **Python 3.11+** - [Download here](https://python.org/downloads)
- **Anthropic API Key** - [Get yours here](https://console.anthropic.com)

### Development Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd giraffe-quality
```

2. **Backend Setup**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
uvicorn app.main:app --reload
```

3. **Frontend Setup** (New terminal)
```bash
cd frontend
npm install
npm run dev
```

4. **Access the application**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Docker Setup (Recommended)

```bash
# Copy environment file
cp backend/.env.example backend/.env
# Edit backend/.env and add your ANTHROPIC_API_KEY

# Start all services
docker-compose up --build
```

## 📊 Default Access

**Admin User:**
- Username: `admin`
- Password: `admin123`

**Manager User:**
- Username: `manager`
- Password: `manager123`

## 🔧 Configuration

### Environment Variables

**Backend (.env):**
```env
DATABASE_URL=sqlite:///./giraffe_quality.db
SECRET_KEY=your-secret-key
ANTHROPIC_API_KEY=your-claude-api-key
DEBUG=true
```

**Frontend:**
```env
VITE_API_URL=http://localhost:8000
```

### Business Configuration

The system comes pre-configured with:

**Branches:**
- חיפה, ראשל״צ, רמה״ח, נס ציונה, לנדמרק, פתח תקווה, הרצליה, סביון

**Dishes:**
- פאד תאי, מלאזית, פיליפינית, אפגנית, קארי דלעת, סצ'ואן, ביף רייס

## 📱 Usage Guide

### Creating Quality Checks
1. Navigate to **Quality Checks** page
2. Click **Add New Check**
3. Select branch, chef, and dish
4. Rate on 1-10 scale (overall + detailed scores)
5. Add notes and photos if needed
6. Submit for immediate analysis

### Viewing Analytics
1. Go to **Dashboard** for overview
2. Use **Analytics** page for AI insights
3. Ask Claude specific questions about your data
4. Generate and export custom reports

### Managing Users (Admin)
1. Access **Settings** → **Users**
2. Create users with appropriate roles
3. Assign branch access permissions
4. Monitor user activity

## 🛡️ Security Features

- **JWT Authentication** - Secure token-based authentication
- **Role-Based Access Control** - Granular permission system
- **Input Validation** - Comprehensive data validation
- **SQL Injection Protection** - SQLAlchemy ORM protection
- **CORS Configuration** - Secure cross-origin requests

## 📈 Performance

- **Optimized Queries** - Efficient database operations
- **Caching Layer** - React Query for client-side caching
- **Lazy Loading** - Code splitting for faster load times
- **Image Optimization** - Compressed uploads and serving

## 🌍 Deployment

### Production Deployment

**Vercel (Frontend):**
1. Connect GitHub repository
2. Set build directory to `frontend`
3. Add environment variable: `VITE_API_URL`

**Railway/Render (Backend):**
1. Connect GitHub repository
2. Set build directory to `backend`
3. Add environment variables (DATABASE_URL, ANTHROPIC_API_KEY, etc.)

### Docker Production
```bash
# Production build
docker-compose -f docker-compose.prod.yml up --build
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests  
cd frontend
npm test
```

## 📚 API Documentation

Full API documentation is available at `/docs` when running the backend server:
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

- `POST /api/v1/auth/login` - User authentication
- `GET /api/v1/dashboard` - Dashboard data
- `POST /api/v1/checks` - Create quality check
- `GET /api/v1/checks` - List quality checks
- `POST /api/v1/dashboard/insights` - AI analysis

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support and questions:
- **GitHub Issues**: [Create an issue](https://github.com/your-repo/issues)
- **Email**: support@giraffe-kitchens.co.il
- **Documentation**: See `/docs` folder for detailed guides

## 🎯 Roadmap

### Upcoming Features
- [ ] Mobile app (React Native)
- [ ] Advanced reporting with charts
- [ ] Integration with POS systems
- [ ] SMS/Email notifications
- [ ] Multi-tenant support
- [ ] Advanced AI features

---

**🦒 Giraffe Kitchens - Quality that starts in the kitchen and ends with satisfied customers**

*Built with ❤️ for the Giraffe restaurant chain*