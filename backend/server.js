const express = require('express');
const cors = require('cors');
const cron = require('node-cron');
const db = require('./database/db');
const fetcher = require('./services/fetcher');

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

// API Endpoints
app.get('/api/articles', (req, res) => {
    try {
        const { limit = 50, offset = 0, source } = req.query;
        let query = 'SELECT * FROM articles';
        const params = [];

        if (source) {
            query += ' WHERE source = ?';
            params.push(source);
        }

        query += ' ORDER BY date DESC LIMIT ? OFFSET ?';
        params.push(limit, offset);

        const articles = db.prepare(query).all(...params);
        res.json(articles);
    } catch (error) {
        console.error('Error fetching articles:', error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});

app.get('/api/entities', (req, res) => {
    try {
        const { limit = 50, type } = req.query;
        let query = `
            SELECT e.*, a.title as article_title, a.url as article_url, a.date as article_date 
            FROM entities e 
            JOIN articles a ON e.article_id = a.id
        `;
        const params = [];

        if (type) {
            query += ' WHERE e.type = ?';
            params.push(type);
        }

        query += ' ORDER BY a.date DESC LIMIT ?';
        params.push(limit);

        const entities = db.prepare(query).all(...params);
        res.json(entities);
    } catch (error) {
        console.error('Error fetching entities:', error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});

app.post('/api/trigger-fetch', async (req, res) => {
    console.log('Manual fetch triggered');
    try {
        await fetcher.run();
        res.json({ message: 'Fetch job started' });
    } catch (error) {
        console.error('Error in manual fetch:', error);
        res.status(500).json({ error: 'Failed to run fetch job' });
    }
});

// Schedule Fetch Job (every hour)
cron.schedule('0 * * * *', () => {
    console.log('Running scheduled fetch job...');
    fetcher.run();
});

// Start Server
app.listen(PORT, () => {
    console.log(`Backend server running on http://localhost:${PORT}`);
    // Run an initial fetch on startup
    fetcher.run();
});
