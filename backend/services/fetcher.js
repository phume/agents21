const Parser = require('rss-parser');
const axios = require('axios');
const cheerio = require('cheerio');
const db = require('../database/db');
const extractor = require('./extractor');

const parser = new Parser();

const SOURCES = [
    {
        name: 'DOJ',
        type: 'rss',
        url: 'https://www.justice.gov/feeds/opa/justice-news.xml' // Example feed, might need adjustment
    },
    {
        name: 'FATF',
        type: 'rss',
        url: 'https://www.fatf-gafi.org/en/pages/rss.xml' // Using generic placeholder, need to verify if specific one exists or use what we found
    },
    {
        name: 'FINTRAC',
        type: 'rss',
        url: 'https://www.fintrac-canafe.gc.ca/rss-eng.xml'
    },
    {
        name: 'DHS',
        type: 'rss',
        url: 'https://www.dhs.gov/news-releases/rss.xml' // Assumption based on search
    },
    {
        name: 'OFAC',
        type: 'scrape',
        url: 'https://ofac.treasury.gov/recent-actions'
    }
];

// Helper to check if article exists
const articleExists = (url) => {
    const row = db.prepare('SELECT id FROM articles WHERE url = ?').get(url);
    return !!row;
};

// Helper to save article and extracted entities
const saveArticle = (source, title, url, date, content) => {
    if (articleExists(url)) {
        console.log(`Skipping existing article: ${title}`);
        return;
    }

    const insert = db.prepare('INSERT INTO articles (source, title, url, date, content) VALUES (?, ?, ?, ?, ?)');
    const info = insert.run(source, title, url, date, content);
    console.log(`Saved article: ${title}`);

    const entities = extractor.extract(content);
    const insertEntity = db.prepare('INSERT INTO entities (name, type, article_id) VALUES (?, ?, ?)');

    entities.forEach(entity => {
        insertEntity.run(entity.name, entity.type, info.lastInsertRowid);
    });
};

const fetchRSS = async (source) => {
    try {
        console.log(`Fetching RSS for ${source.name}...`);
        const feed = await parser.parseURL(source.url);

        for (const item of feed.items) {
            // Some feeds might differ in fields
            const title = item.title;
            const url = item.link;
            const date = item.isoDate || item.pubDate;
            const content = item.contentSnippet || item.content || '';

            saveArticle(source.name, title, url, date, content);
        }
    } catch (error) {
        console.error(`Error fetching RSS for ${source.name}:`, error.message);
    }
};

const fetchOFAC = async (source) => {
    try {
        console.log(`Scraping OFAC...`);
        const { data } = await axios.get(source.url);
        const $ = cheerio.load(data);

        // Select the recent actions list items. 
        // Note: Selector is an approximation, might need adjustment based on actual DOM
        $('.views-row').each((i, el) => {
            const dateText = $(el).find('time').attr('datetime') || $(el).find('.date-display-single').text().trim();
            const linkEl = $(el).find('a').first();
            const title = linkEl.text().trim();
            const relativeUrl = linkEl.attr('href');
            const url = relativeUrl ? new URL(relativeUrl, source.url).href : '';

            // For content, we might need to visit the link or just use the title/snippet if available
            // For now, let's use the title as content since OFAC titles are descriptive
            const content = title;

            if (title && url) {
                saveArticle(source.name, title, url, dateText, content);
            }
        });

    } catch (error) {
        console.error(`Error scraping OFAC:`, error.message);
    }
};

const run = async () => {
    console.log('Starting fetch job...');
    for (const source of SOURCES) {
        if (source.type === 'rss') {
            await fetchRSS(source);
        } else if (source.type === 'scrape') {
            await fetchOFAC(source);
        }
    }
    console.log('Fetch job completed.');
};

module.exports = { run };
