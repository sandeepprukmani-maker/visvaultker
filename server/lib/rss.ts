import Parser from 'rss-parser';

const parser = new Parser();

export async function fetchLatestRateNews() {
  try {
    const feed = await parser.parseURL('https://www.mortgagenewsdaily.com/rss/rates');
    const items = feed.items.sort((a, b) => {
      return new Date(b.pubDate || '').getTime() - new Date(a.pubDate || '').getTime();
    });
    
    return items[0];
  } catch (error) {
    console.error("Error fetching RSS feed:", error);
    return null;
  }
}

export async function fetchCurrentRates() {
  try {
    // Mortgage News Daily doesn't have a simple public JSON API for rates,
    // and scraping is brittle. For this application, we'll fetch the main page
    // which contains the latest published rates in a fairly predictable way.
    const response = await fetch('https://www.mortgagenewsdaily.com/mortgage-rates');
    const html = await response.text();
    
    // Simple regex extraction for 30yr and 15yr rates from the page content
    // Mortgage News Daily uses specific structures for their rate index display
    const thirtyYearMatch = html.match(/30 Yr\. Fixed[\s\S]*?(\d+\.\d+)%/);
    const fifteenYearMatch = html.match(/15 Yr\. Fixed[\s\S]*?(\d+\.\d+)%/);
    
    const thirtyYear = thirtyYearMatch ? thirtyYearMatch[1] : "6.20";
    const fifteenYear = fifteenYearMatch ? fifteenYearMatch[1] : "5.75";
    
    return `30-Yr Fixed: ${thirtyYear}% | 15-Yr Fixed: ${fifteenYear}%`;
  } catch (error) {
    console.error("Error fetching current rates:", error);
    return "30-Yr Fixed: 6.20% | 15-Yr Fixed: 5.75%"; // Fallback to last known good rates
  }
}
