# The Silent Cartographer

Transform Kindle highlight exports into a structured knowledge management system in Obsidian, with Asana task integration and email notifications.

## Features

- **Parse Kindle HTML exports** - Extract highlights with color-coded meanings
- **AI-powered concept extraction** - Use Claude to identify key concepts from yellow highlights
- **Action item creation** - Convert pink highlights into Asana tasks
- **Beautiful quotes & disagreements** - Store blue and orange highlights in book notes
- **Obsidian integration** - Generate structured notes with backlinks and templates
- **Spaced repetition** - Track concepts for review at optimal intervals
- **Email notifications** - Receive summaries after processing and review reminders

## Highlight Colors

| Color | Meaning | Processing |
|-------|---------|------------|
| 🟡 Yellow | Key concepts | Extract top 10 → Create concept notes with full template analysis |
| 🩷 Pink | Action items | Extract top 3 → Create Asana tasks |
| 🔵 Blue | Beautiful quotes | Store in book note's quotes section |
| 🟠 Orange | Disagreements | Store in book note with space for your thoughts |

## Installation

### Prerequisites

- Python 3.11 or higher
- An Anthropic API key (for Claude)
- (Optional) Asana personal access token
- (Optional) SMTP credentials for email notifications

### Setup

1. **Clone or download** this repository to your preferred location.

2. **Install dependencies:**
   ```bash
   cd "C:\Users\YOUR_USER\Documents\The Silent Cartographer"
   pip install -e .
   ```

3. **Configure settings:**
   Edit `config.env` with your credentials:
   ```env
   # Anthropic API (required)
   ANTHROPIC_API_KEY=your-api-key-here

   # Asana (optional - for task creation)
   ASANA_ACCESS_TOKEN=your-token
   ASANA_WORKSPACE_GID=your-workspace-id
   ASANA_PROJECT_GID=your-project-id

   # Email (optional - for notifications)
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   TSC_EMAIL_TO=your-email@gmail.com
   ```

4. **Create required folders** (if they don't exist):
   ```bash
   mkdir "C:\Users\YOUR_USER\Documents\The Library\Books"
   mkdir "C:\Users\YOUR_USER\Documents\The Library\Ideas"
   mkdir "C:\Users\YOUR_USER\Documents\Kindle Exports\processed"
   ```

## Usage

### Process Kindle Exports

1. **Export highlights from Kindle:**
   - Open Kindle for PC/Mac
   - Go to your book's notebook
   - Click "Export" to save as HTML
   - Save to `C:\Users\YOUR_USER\Documents\Kindle Exports\`

2. **Run the processor:**
   ```bash
   # Process all new HTML files
   tsc process

   # Process a specific file
   tsc process --file "path/to/export.html"

   # Preview without writing (dry run)
   tsc process --dry-run

   # Skip Asana tasks or email
   tsc process --skip-asana --skip-email
   ```

### View Dashboard

```bash
# Show statistics in terminal
tsc dashboard

# Output as JSON
tsc dashboard --format json
```

### Send Digests

```bash
# Weekly summary
tsc digest --type weekly

# Monthly analytics
tsc digest --type monthly

# Spaced repetition reminders
tsc digest --type spaced

# Preview without sending
tsc digest --type weekly --dry-run
```

## Workflow

1. **Read a book** on Kindle, highlighting as you go:
   - Yellow: Key concepts you want to deeply understand
   - Pink: Actions you want to take based on what you read
   - Blue: Beautiful quotes worth preserving
   - Orange: Ideas you disagree with or want to challenge

2. **Export highlights** from Kindle to HTML

3. **Run `tsc process`** to:
   - Parse the HTML and extract highlights by color
   - Use AI to identify top 10 concepts from yellow highlights
   - Create detailed concept notes using the template framework
   - Use AI to extract top 3 actionable tasks from pink highlights
   - Create Asana tasks with book context
   - Generate a book note with all sections and backlinks
   - Send you an email summary
   - Move the processed file to `processed/` folder

4. **Review in Obsidian**:
   - Book notes appear in `The Library/Books/`
   - Concept notes appear in `The Library/Ideas/`
   - Backlinks connect everything together

5. **Spaced repetition**:
   - Run `tsc digest --type spaced` to see concepts due for review
   - Open the concept notes in Obsidian and reinforce your learning

## Scheduling (Windows Task Scheduler)

To run TSC automatically on a schedule:

1. Open Task Scheduler
2. Create Basic Task:
   - Name: "TSC Weekly Digest"
   - Trigger: Weekly (your preferred day/time)
   - Action: Start a program
   - Program: `python` (or full path to Python)
   - Arguments: `-m tsc digest --type spaced`
   - Start in: `C:\Users\YOUR_USER\Documents\The Silent Cartographer`

3. Repeat for other scheduled tasks as needed

## File Structure

```
The Silent Cartographer/
├── tsc/                    # Main package
│   ├── cli.py              # Command-line interface
│   ├── config.py           # Configuration loader
│   ├── parsers/            # HTML parsing
│   ├── processors/         # Concept & action extraction
│   ├── generators/         # Note generation
│   ├── integrations/       # External APIs
│   └── memory/             # State tracking
├── profile.md              # Your context for AI
├── template.md             # Concept note template
├── config.env              # Configuration
├── .memory.json            # Processing state (auto-generated)
└── README.md               # This file

The Library/                # Obsidian vault
├── Books/                  # Book notes
└── Ideas/                  # Concept notes

Kindle Exports/             # Drop HTML exports here
└── processed/              # Completed exports
```

## Troubleshooting

### "ANTHROPIC_API_KEY not configured"
Make sure you've set your API key in `config.env`. The key should start with `sk-ant-`.

### "No HTML files found in Kindle directory"
Check that:
- HTML files are in `C:\Users\YOUR_USER\Documents\Kindle Exports\`
- Files haven't already been processed (moved to `processed/`)

### "Email not configured"
Email is optional. To enable it, set all SMTP variables in `config.env`.
For Gmail, you'll need to create an [App Password](https://support.google.com/accounts/answer/185833).

### Highlights not being detected
The parser expects Kindle's standard HTML export format. If your export looks different:
- Check the HTML structure matches expected classes
- Yellow/pink/blue/orange highlights need corresponding CSS classes

### Asana tasks not created
Verify your Asana configuration:
- `ASANA_ACCESS_TOKEN`: Get from [Asana Developer Console](https://app.asana.com/0/developer-console)
- `ASANA_WORKSPACE_GID`: Find in URL when viewing workspace
- `ASANA_PROJECT_GID`: Find in URL when viewing project

## License

Personal use project by Carlos for the Hermes AI knowledge management system.
