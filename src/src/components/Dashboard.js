import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { restaurantsAPI } from '../services/api';

const Dashboard = () => {
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const userType = localStorage.getItem('userType');

  useEffect(() => {
    fetchRestaurants();
  }, []);

  const fetchRestaurants = async () => {
    try {
      const response = await restaurantsAPI.getAll();
      setRestaurants(response.data);
    } catch (err) {
      console.error('Error fetching restaurants:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <div>טוען נתונים...</div>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <header style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '30px',
        padding: '20px',
        background: 'white',
        borderRadius: '15px',
        boxShadow: '0 4px 16px rgba(0,0,0,0.1)'
      }}>
        <h1>🦒 מערכת ניהול מטבח</h1>
        <button 
          onClick={handleLogout}
          style={{
            padding: '8px 16px',
            backgroundColor: '#f44336',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer'
          }}
        >
          יציאה
        </button>
      </header>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '20px'
      }}>
        {restaurants.map(restaurant => (
          <div 
            key={restaurant.id}
            style={{
              background: 'white',
              padding: '20px',
              borderRadius: '15px',
              boxShadow: '0 4px 16px rgba(0,0,0,0.1)',
              cursor: 'pointer'
            }}
            onClick={() => navigate(`/restaurant/${restaurant.id}`)}
          >
            <h3>{restaurant.name}</h3>
            <p>מזהה: {restaurant.id}</p>
            <p>סטטוס: {restaurant.is_active ? '✅ פעיל' : '❌ לא פעיל'}</p>
            <div style={{ marginTop: '10px', color: '#666', fontSize: '14px' }}>
              לחץ לפרטים נוספים ←
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;
