// pages/api/podcast-feed.js
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import moment from 'moment';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default function handler(req, res) {
    try {
        // Set proper content type for RSS
        res.setHeader('Content-Type', 'application/xml');
        
        // Generate the feed dynamically based on available episodes
        const rssFeed = generatePodcastFeed();
        
        res.status(200).send(rssFeed);
    } catch (error) {
        console.error('Error generating podcast feed:', error);
        res.status(500).send('Error generating podcast feed');
    }
}

function generateEpisodeEntries() {
    try {
        const publicDir = path.join(process.cwd(), 'public');
        const files = fs.readdirSync(publicDir);
        
        // Filter for MP3 files with date format YYYY-MM-DD.mp3
        const episodes = files
            .filter(file => /^\d{4}-\d{2}-\d{2}\.mp3$/.test(file))
            .sort((a, b) => b.localeCompare(a)) // Sort newest first
            .map(file => {
                const date = file.replace('.mp3', '');
                const pubDate = moment(date).format('ddd, DD MMM YYYY HH:mm:ss ZZ');
                const title = `SA News for ${moment(date).format('D MMM YYYY')}`;
                
                return `
                    <item>
                        <title>${title}</title>
                        <description>Your daily update on South African news.</description>
                        <pubDate>${pubDate}</pubDate>
                        <enclosure url="/public/${file}" type="audio/mpeg" length="0"/>
                        <guid isPermaLink="false">${date}</guid>
                        <itunes:duration>00:05:00</itunes:duration>
                    </item>
                `;
            })
            .join('\n');
            
        return episodes;
    } catch (error) {
        console.error('Error generating episode entries:', error);
        return '<!-- Error generating episode entries -->';
    }
}

function generatePodcastFeed() {
    return `<?xml version="1.0" encoding="UTF-8"?>
    <rss xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" version="2.0">
        <channel>
            <title>Mzansi Lowdown: South African Daily News</title>
            <link>https://letstalkaitools.com</link>
            <language>en-za</language>
            <itunes:author>Let's Talk AI Tools</itunes:author>
            <description>Stay informed on South Africa's most important stories with our concise daily news podcast. In just 3-5 minutes each day, our AI podcast service collects &amp; delivers headlines and key developments from trusted local news sources, including the Daily Maverick, Sunday Times, and Mail &amp; Guardian.</description>
            <itunes:image href="/public/daily_news_icon.jpg"/>
            <itunes:category text="News"/>
            <itunes:explicit>no</itunes:explicit>
            
            <!-- Episodes -->
            ${generateEpisodeEntries()}
            
        </channel>
    </rss>`;
}