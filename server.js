const express = require('express');
const app = express();
const PORT = 3000;

app.use(express.json());
app.use(express.static('public'));

app.get('/', (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>Sistema de Inventario PTAR</title>
      <meta charset="UTF-8">
      <style>
        body {
          font-family: Arial, sans-serif;
          max-width: 800px;
          margin: 50px auto;
          padding: 20px;
          background: #f5f5f5;
        }
        .container {
          background: white;
          padding: 30px;
          border-radius: 10px;
          box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
          color: #2c3e50;
          border-bottom: 3px solid #3498db;
          padding-bottom: 10px;
        }
        .info {
          background: #ecf0f1;
          padding: 15px;
          border-radius: 5px;
          margin: 20px 0;
        }
        .status {
          color: #27ae60;
          font-weight: bold;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>🏭 Sistema de Inventario PTAR</h1>
        <div class="info">
          <p class="status">✅ Servidor funcionando correctamente</p>
          <p><strong>Versión:</strong> 1.0.0</p>
          <p><strong>Estado:</strong> Activo</p>
        </div>
        <h2>Bienvenido</h2>
        <p>Este es el servidor del sistema de inventario para las plantas de tratamiento de agua.</p>
        <p>Desarrollado por Juan - Depto. de Saneamiento</p>
      </div>
    </body>
    </html>
  `);
});

app.get('/api/status', (req, res) => {
  res.json({
    status: 'ok',
    message: 'Servidor funcionando',
    timestamp: new Date()
  });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`✅ Servidor corriendo en puerto ${PORT}`);
  console.log(`📍 Acceso local: http://localhost:${PORT}`);
});