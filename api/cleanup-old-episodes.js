// ABOUTME: Cleanup old podcast episodes API endpoint
// ABOUTME: Removes podcast episodes older than 30 days to manage storage

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { readFileSync } from 'fs';
import { join } from 'path';

console.log('Starting cleanup-old-episodes.js script...');

// Load secrets from secure location
function loadSecrets() {
  try {
    const homeDir = process.env.HOME || process.env.USERPROFILE;
    const secretsPath = join(homeDir, '.config', 'sa-podcast', 'secrets.json');
    const secrets = JSON.parse(readFileSync(secretsPath, 'utf8'));
    return secrets;
  } catch (error) {
    console.error('Failed to load secrets:', error.message);
    process.exit(1);
  }
}

const secrets = loadSecrets();

function isOldEpisode(filename, cutoffDate) {
  // Match files like 2025-04-12.mp3
  const match = filename.match(/^(\d{4}-\d{2}-\d{2})\.mp3$/);
  if (!match) return false;
  const fileDate = new Date(match[1]);
  return fileDate < cutoffDate;
}

async function cleanupOldEpisodes() {
  const episodesDir = path.join(process.cwd(), 'public');
  console.log('Resolved episodesDir:', episodesDir);
  console.log('episodesDir exists:', fs.existsSync(episodesDir));

  if (!fs.existsSync(episodesDir)) {
    console.log('Episodes directory does not exist. Exiting.');
    return;
  }

  const files = fs.readdirSync(episodesDir);
  console.log('Files in episodesDir:', files);

  // Calculate cutoff date (30 days ago)
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - 30);
  console.log('Cutoff date:', cutoffDate.toISOString().slice(0, 10));

  // Find and delete old episodes
  let deletedCount = 0;
  for (const file of files) {
    if (isOldEpisode(file, cutoffDate)) {
      try {
        fs.unlinkSync(path.join(episodesDir, file));
        console.log(`Deleted old episode: ${file}`);
        deletedCount++;
      } catch (err) {
        console.error(`Failed to delete ${file}:`, err);
      }
    }
  }
  console.log(`Cleanup complete. Deleted ${deletedCount} old episodes.`);
}

// API endpoint handler
export default async function handler(req, res) {
  if (req.query.key !== secrets.cleanup.secret_key) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  await cleanupOldEpisodes();
  return res.status(200).json({ status: 'Cleanup complete' });
}

// Run as script if called directly
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  cleanupOldEpisodes()
    .then(() => process.exit(0))
    .catch(err => {
      console.error('Cleanup failed:', err);
      process.exit(1);
    });
}