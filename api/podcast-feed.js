// Generate podcast RSS feed
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import moment from 'moment';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Export the handler for API route usage
export default async function handler(req, res) {
    try {
        // Set proper content type for RSS
        res.setHeader('Content-Type', 'application/xml');
        
        // Serve the static feed.xml file
        const feedPath = path.join(process.cwd(), 'public', 'feed.xml');
        if (fs.existsSync(feedPath)) {
            const feed = fs.readFileSync(feedPath, 'utf-8');
            res.status(200).send(feed);
        } else {
            console.error('Feed file not found:', feedPath);
            res.status(404).send('<!-- Feed file not found. Please wait for the next scheduled update. -->');
        }
    } catch (error) {
        console.error('Error serving podcast feed:', error);
        res.status(500).send('Error serving podcast feed');
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
                const stats = fs.statSync(path.join(publicDir, file));
                
                return `
                    <item>
                        <title>${title}</title>
                        <description>Your daily update on South African news.</description>
                        <pubDate>${pubDate}</pubDate>
                        <enclosure url="https://sa-news-podcast.vercel.app/${file}" type="audio/mpeg" length="${stats.size}"/>
                        <guid isPermaLink="false">${date}</guid>
                        <itunes:duration>00:05:00</itunes:duration>
                    </item>
                `;
            })
            .join('\n');
            
        if (!episodes) {
            console.error('No episodes found in directory:', publicDir);
            console.log('Directory contents:', fs.readdirSync(publicDir));
        }
        
        return episodes;
    } catch (error) {
        console.error('Error generating episode entries:', error);
        console.error('Error details:', error.message);
        if (error.code === 'ENOENT') {
            console.error('Directory not found:', path.join(process.cwd(), 'public'));
        }
        return '<!-- Error generating episode entries -->';
    }
}

function generatePodcastFeed() {
    const episodes = generateEpisodeEntries();
    console.log('Generated episodes:', episodes ? 'Yes' : 'No');
    
    return `<?xml version="1.0" encoding="UTF-8"?>
    <rss xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" version="2.0">
        <channel>
            <title>Mzansi Lowdown: South African Daily News</title>
            <link>https://sa-news-podcast.vercel.app</link>
            <language>en-za</language>
            <itunes:author>Let's Talk AI Tools</itunes:author>
            <description>Stay informed on South Africa's most important stories with our concise daily news podcast. In just 3-5 minutes each day, our AI podcast service collects &amp; delivers headlines and key developments from trusted local news sources, including the Daily Maverick, Sunday Times, and Mail &amp; Guardian.</description>
            <itunes:image href="https://sa-news-podcast.vercel.app/daily_news_icon.jpg"/>
            <itunes:category text="News"/>
            <itunes:explicit>no</itunes:explicit>
            
            <!-- Episodes -->
            ${episodes}
            
        </channel>
    </rss>`;
}

// Run as script if called directly
if (process.argv[1] === fileURLToPath(import.meta.url)) {
    try {
        const feed = generatePodcastFeed();
        const outputPath = path.join(process.cwd(), 'public', 'feed.xml');
        fs.writeFileSync(outputPath, feed);
        console.log(`Feed generated successfully at ${outputPath}`);
    } catch (error) {
        console.error('Error writing feed:', error);
        process.exit(1);
    }
}