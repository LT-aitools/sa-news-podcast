// Generate podcast RSS feed
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import moment from 'moment';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const baseUrl = 'https://mzansi-podcast.letstalkaitools.com';

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
                
                return {
                    title,
                    description: 'Your daily update on South African news.',
                    pubDate,
                    filename: file,
                    guid: date,
                    duration: '00:05:00',
                    length: stats.size
                };
            });
            
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
        return [];
    }
}

function generatePodcastFeed(episodes) {
    const feed = `<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>Mzansi Lowdown: South African Daily News</title>
    <link>${baseUrl}</link>
    <description>Stay informed on South Africa's most important stories with our concise daily news podcast. In just 3-5 minutes each day, our AI podcast service collects and delivers headlines and key developments from trusted local news sources, including the Daily Maverick, Sunday Times, and Mail &amp; Guardian.</description>
    <language>en</language>
    <itunes:author>Let's Talk AI Tools</itunes:author>
    <itunes:owner>
      <itunes:name>Let's Talk AI Tools</itunes:name>
      <itunes:email>hello@letstalkaitools.com</itunes:email>
    </itunes:owner>
    <managingEditor>hello@letstalkaitools.com (Let's Talk AI Tools)</managingEditor>
    <itunes:type>episodic</itunes:type>
    <itunes:category text="News" />
    <itunes:image href="${baseUrl}/daily_news_icon.jpg" />
    <itunes:explicit>false</itunes:explicit>
    <!-- Episodes -->
    ${episodes.map(episode => `
    <item>
      <title>${episode.title}</title>
      <description>${episode.description}</description>
      <pubDate>${episode.pubDate}</pubDate>
      <guid isPermaLink="false">${episode.guid}</guid>
      <itunes:duration>${episode.duration}</itunes:duration>
      <enclosure 
        url="${baseUrl}/${episode.filename}"
        type="audio/mpeg"
        length="${episode.length}"
      />
    </item>`).join('\n    ')}
  </channel>
</rss>`;

  return feed;
}

// Run as script if called directly
if (process.argv[1] === fileURLToPath(import.meta.url)) {
    try {
        const episodes = generateEpisodeEntries();
        const feed = generatePodcastFeed(episodes);
        const outputPath = path.join(process.cwd(), 'public', 'feed.xml');
        fs.writeFileSync(outputPath, feed);
        console.log(`Feed generated successfully at ${outputPath}`);
    } catch (error) {
        console.error('Error writing feed:', error);
        process.exit(1);
    }
}