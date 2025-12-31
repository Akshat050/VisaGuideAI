# ✈️ VisaGuideAI

> Route-aware visa assistant with verified requirements, context-grounded AI chat, and document completeness checks

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=black)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?logo=postgresql&logoColor=white)](https://www.postgresql.org/)

## 📋 Overview

VisaGuideAI is an intelligent visa assistance platform that helps travelers navigate the complex world of visa requirements. Using advanced AI and real-time data, it provides personalized guidance for visa applications based on your travel route, nationality, and specific circumstances.

### ✨ Key Features

- 🗺️ **Route-Aware Analysis** - Intelligent visa requirement detection based on your complete travel itinerary
- 🤖 **AI-Powered Chat** - Context-grounded conversational assistant powered by Gemini AI
- 📄 **Document Verification** - Automated completeness checks for visa applications
- ✅ **Verified Requirements** - Up-to-date visa information from official sources
- 🔄 **Real-Time Processing** - Fast responses with Redis caching
- 🌍 **Multi-Country Support** - Comprehensive database of visa requirements

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   React     │◄────►│   FastAPI    │◄────►│ PostgreSQL  │
│  Frontend   │      │   Backend    │      │  Database   │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │    Redis     │
                     │    Cache     │
                     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  Gemini AI   │
                     │   Service    │
                     └──────────────┘
```

## 🚀 Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **PostgreSQL** - Reliable relational database
- **Redis** - In-memory caching for fast responses
- **SQLAlchemy** - ORM for database operations
- **Pydantic** - Data validation and settings management

### Frontend
- **React** - Component-based UI library
- **Vite** - Next-generation frontend tooling
- **Axios** - HTTP client for API communication
- **React Router** - Client-side routing
- **TailwindCSS** - Utility-first CSS framework

### AI Integration
- **Google Gemini AI** - Advanced language model for intelligent responses
- **LangChain** - Framework for building AI applications

## 📦 Installation

### Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL 13+
- Redis 6+

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/Akshat050/VisaGuideAI.git
cd VisaGuideAI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
alembic upgrade head

# Run the backend
uvicorn main:app --reload
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your API endpoint

# Run the development server
npm run dev
```

## ⚙️ Configuration

Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/visaguideai

# Redis
REDIS_URL=redis://localhost:6379

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here

# Application
SECRET_KEY=your_secret_key_here
DEBUG=True
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## 🎯 Usage

### Starting a Visa Query

```python
# Example API request
POST /api/visa/check
{
  "nationality": "IN",
  "destination": "US",
  "travel_dates": {
    "departure": "2024-03-15",
    "return": "2024-03-30"
  },
  "purpose": "tourism"
}
```

### Using the AI Chat

```python
# Example chat request
POST /api/chat
{
  "message": "What documents do I need for a US tourist visa?",
  "context": {
    "nationality": "IN",
    "visa_type": "B-2"
  }
}
```

## 📸 Screenshots

### Home Page
*Coming soon*

### Visa Requirements Dashboard
*Coming soon*

### AI Chat Interface
*Coming soon*

## 🧪 Testing

```bash
# Run backend tests
pytest

# Run frontend tests
npm test

# Run with coverage
pytest --cov=app tests/
```

## 📚 API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🛣️ Roadmap

- [ ] Multi-language support
- [ ] Mobile application (React Native)
- [ ] Visa application tracking
- [ ] Integration with embassy appointment systems
- [ ] Travel insurance recommendations
- [ ] Flight and accommodation suggestions

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Akshat**
- GitHub: [@Akshat050](https://github.com/Akshat050)
- LinkedIn: [LinkedIn](http://www.linkedin.com/in/akshat-bhatt)

## 🙏 Acknowledgments

- Google Gemini AI for powering intelligent responses
- FastAPI community for excellent documentation
- All contributors who help improve this project

## 📞 Support

If you have any questions or need help, please:
- Open an issue on GitHub
- Contact me via email: your.email@example.com

---

<div align="center">

**Made with ❤️ by Akshat**

If you found this project helpful, please consider giving it a ⭐

</div>
