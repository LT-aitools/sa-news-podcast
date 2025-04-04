// pages/api/cleanup-old-episodes.js
import fs from 'fs';
import path from 'path';

export default async function handler(req, res) {
  // Secure this endpoint with a secret key
  if (req.query.key !== process.env.CLEANUP_SECRET_KEY) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  const episodesDir = path.join(process.cwd(), 'public/episodes');
  const metadataPath = path.join(process.cwd(), 'data/episodes-metadata.json');
  
  // Read metadata
  const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
  
  // Calculate cutoff date (30 days ago)
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - 30);
  
  // Find episodes to delete
  const expiredEpisodes = metadata.episodes.filter(
    episode => new Date(episode.uploadDate) < cutoffDate
  );
  
  // Delete files
  for (const episode of expiredEpisodes) {
    try {
      fs.unlinkSync(path.join(episodesDir, episode.filename));
      console.log(`Deleted ${episode.filename}`);
    } catch (err) {
      console.error(`Failed to delete ${episode.filename}:`, err);
    }
  }
  
  // Update metadata
  metadata.episodes = metadata.episodes.filter(
    episode => new Date(episode.uploadDate) >= cutoffDate
  );
  fs.writeFileSync(metadataPath, JSON.stringify(metadata, null, 2));
  
  return res.status(200).json({ 
    deleted: expiredEpisodes.length,
    remaining: metadata.episodes.length
  });
}