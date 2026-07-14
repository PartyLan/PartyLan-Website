export const siteContent = {
  brand: {
    name: 'Party.LAN',
    tagline: 'Plug in. Party on.',
    description:
      'A bright, community-first homepage foundation for local LAN events, tournaments, tabletop corners, creator showcases, and sponsor activations.',
  },
  navigation: ['Experience', 'Schedule', 'Tournaments', 'Sponsors', 'FAQ'],
  hero: {
    eyebrow: 'Homepage foundation prototype',
    headline: 'The local multiplayer weekend built for every kind of player.',
    body:
      'Party.LAN brings competitive brackets, casual free play, community creators, and late-night hangouts into one welcoming event hub.',
    actions: [
      { label: 'View sections', href: '#sections' },
      { label: 'Review placeholders', href: '#placeholders', variant: 'secondary' },
    ],
    stats: [
      { value: '24+', label: 'hours of play' },
      { value: '8', label: 'content sections' },
      { value: '2', label: 'theme modes' },
    ],
  },
  sections: [
    {
      title: 'Event Overview',
      description: 'Clear positioning for what Party.LAN is, who it serves, and why attendees should care.',
    },
    {
      title: 'Featured Experiences',
      description: 'Cards for tournaments, free play, tabletop, creator streams, food, and community spaces.',
    },
    {
      title: 'Schedule Preview',
      description: 'A data-driven timeline that can be replaced with confirmed dates, doors, and bracket times.',
    },
    {
      title: 'Tournament Highlights',
      description: 'Reusable game cards for title, format, prize note, registration status, and skill level.',
    },
    {
      title: 'Venue & Bring List',
      description: 'Practical arrival information, BYOC guidance, network expectations, and accessibility notes.',
    },
    {
      title: 'Sponsor Strip',
      description: 'Placeholder sponsor tiers and logo areas ready for partner confirmation.',
    },
    {
      title: 'FAQ',
      description: 'Owner-editable questions for tickets, age policy, gear, food, refunds, and streaming.',
    },
    {
      title: 'Final CTA',
      description: 'Conversion area for tickets, Discord, volunteer signup, and newsletter paths.',
    },
  ],
  experiences: [
    'BYOC and house systems',
    'Competitive brackets',
    'Casual party games',
    'Tabletop and chill zone',
    'Creator stream desk',
    'Sponsor challenges',
  ],
  schedule: [
    { time: 'Friday 6:00 PM', title: 'Doors, check-in, network setup' },
    { time: 'Friday 8:30 PM', title: 'Opening party games and free play' },
    { time: 'Saturday 11:00 AM', title: 'Main tournament blocks begin' },
    { time: 'Saturday 7:00 PM', title: 'Creator showcase and sponsor challenges' },
    { time: 'Sunday 12:00 PM', title: 'Finals, awards, teardown' },
  ],
  tournaments: [
    { game: 'Fighting Game Bracket', format: 'Double elimination', status: 'Needs title confirmation' },
    { game: 'Team Shooter Cup', format: '5v5 pools into finals', status: 'Needs prize confirmation' },
    { game: 'Party Game Gauntlet', format: 'Drop-in leaderboard', status: 'Prototype ready' },
  ],
  placeholders: [
    'Final event date, venue address, and ticketing URL',
    'Confirmed tournament titles, rulesets, and prize language',
    'Sponsor names, logos, tiers, and legal copy',
    'Organizer-approved photography, safety, refund, and age policies',
    'Discord, volunteer, streaming, and newsletter links',
  ],
};
