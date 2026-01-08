const Database = require('better-sqlite3');
const path = require('path');

const dbPath = path.join(__dirname, 'aml.db');
const db = new Database(dbPath, { verbose: console.log });

// Initialize tables
const initDb = () => {
    db.exec(`
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            date TEXT,
            content TEXT
        );

        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            article_id INTEGER,
            FOREIGN KEY(article_id) REFERENCES articles(id)
        );
    `);
    console.log('Database tables initialized');
};

initDb();

module.exports = db;
