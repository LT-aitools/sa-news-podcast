// pages/api/podcast-feed.js
export default function handler(req, res) {
    // Set proper content type for RSS
    res.setHeader('Content-Type', 'application/xml');
    
    // Generate the feed dynamically based on available episodes
    const rssFeed = generatePodcastFeed();
    
    res.status(200).send(rssFeed);
  }
  
  function generatePodcastFeed() {
    // Generate valid podcast RSS XML here
    // Only include episodes that are within your retention window
    
    return `<?xml version="1.0" encoding="UTF-8"?>
    <rss xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" version="2.0">
      <channel>
        <title>Mzansi Lowdown: South African Daily News</title>
        <link>https://letstalkaitools.com</link>
        <language>en-za</language>
        <itunes:author>Let's Talk AI Tools</itunes:author>
        <description>Stay informed on South Africa's most important stories with our concise daily news podcast. In just 3-5 minutes each day, our AI podcast service collects & delivers headlines and key developments from trusted local news sources, including the Daily Maverick, Sunday Times, and Mail & Guardian. 
          <br></br>
          NOTE: This podcast is a personal project from the not-for-profit Let's Talk AI Tools (www.letstalkaitools.com). We're two product gals (and our chatbots) building things with  generative AI. To keep hosting costs low, we only keep the last 30 days of episodes (and auto-delete any previous ones). 
        </description>
        <itunes:image href="/public/daily_news_icon.jpg"/>
        
        <!-- Episodes here, dynamically generated -->
        ${generateEpisodeEntries()}
        
      </channel>
    </rss>`;
  }