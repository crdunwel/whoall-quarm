import React, { useState, useEffect } from 'react';
import './App.css';
import initSqlJs from 'sql.js';

function App() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [db, setDb] = useState(null);
  const [form, setForm] = useState({
    level_start: '',
    level_end: '',
    class_: '',
    name: '',
    race: '',
    guild: '',
    zone: '',
    lfg: false,
    last_updated: '' // Adding the last_updated field here, though you may not need it for input forms
  });

  useEffect(() => {
      async function fetchDataAndInitializeDb() {
          // Fetch JSON data from endpoint
          const response = await fetch('/path/to/json/endpoint');
          const jsonData = await response.json();

          // Initialize SQLite database if it hasn't been initialized
          if (!db) {
              const SQL = await initSqlJs();
              setDb(new SQL.Database());
          }

          // Insert or update data in SQLite database
          jsonData.forEach(player => {
              // Assuming player has a last_updated field in YYYY-MM-DD HH:MM:SS format
              const currentTimestamp = new Date(player.last_updated).getTime();
              const existingRecord = db.exec(`SELECT last_updated FROM players WHERE name='${player.name}'`);

              if (existingRecord[0] && existingRecord[0].values.length > 0) {
                  const existingTimestamp = new Date(existingRecord[0].values[0][0]).getTime();

                  // Update only if newer data is available
                  if (currentTimestamp > existingTimestamp) {
                      db.run(`UPDATE players SET level=?, class=?, race=?, guild=?, zone=?, lfg=?, last_updated=? WHERE name=?`,
                          [player.level, player.class, player.race, player.guild, player.zone, player.lfg, player.last_updated, player.name]);
                  }
              } else {
                  // Insert if not existing
                  db.run(`INSERT INTO players (level, class, name, race, guild, zone, lfg, last_updated) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
                      [player.level, player.class, player.name, player.race, player.guild, player.zone, player.lfg, player.last_updated]);
              }
          });

          setLoading(false);
      }

      fetchDataAndInitializeDb();

      // Set a timer to fetch data every minute
      const intervalId = setInterval(fetchDataAndInitializeDb, 60 * 1000);  // 60 * 1000ms = 1 minute

      // Clean up the interval on component unmount
      return () => clearInterval(intervalId);

  }, [db]);  // dependency on db so that the useEffect doesn't run every time db changes

  const handleSearch = () => {
      if (!db) return;  // Make sure db is available

      // Construct query (simplified for demonstration)
      let query = "SELECT * FROM players WHERE 1=1";
      if(form.level_start && form.level_end) {
        query += ` AND level BETWEEN ${form.level_start} AND ${form.level_end}`;
      }
      // ... add other conditions

      // Execute the query
      const results = db.exec(query);

      const columns = results[0].columns;  // This gives you the column names
        setData(results[0].values.map(row => {
            let obj = {};
            columns.forEach((col, index) => {
                obj[col.toLowerCase()] = row[index];  // Using toLowerCase to make it more JS-friendly
            });
            return obj;
        }));
      // // Set the data to state
      // setData(results[0].values);  // Make sure to grab the actual result values
  };

  const handleInputChange = (event) => {
    const target = event.target;
    const value = target.type === 'checkbox' ? target.checked : target.value;
    const name = target.name;

    setForm(prevForm => ({
      ...prevForm,
      [name]: value
    }));
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="App">
      <h1>Player Query</h1>

      <div className="inputs">
        {/* Updated each input field to use value and onChange from state */}
        <label>
          Level Start:
          <input type="number" name="level_start" value={form.level_start} onChange={handleInputChange} />
        </label>
        <label>
          Level End:
          <input type="number" name="level_end" value={form.level_end} onChange={handleInputChange} />
        </label>
        <label>
          Class:
          <input type="text" name="class_" value={form.class_} onChange={handleInputChange} />
        </label>
        <label>
          Name:
          <input type="text" name="name" value={form.name} onChange={handleInputChange} />
        </label>
        <label>
          Race:
          <input type="text" name="race" value={form.race} onChange={handleInputChange} />
        </label>
        <label>
          Guild:
          <input type="text" name="guild" value={form.guild} onChange={handleInputChange} />
        </label>
        <label>
          Zone:
          <input type="text" name="zone" value={form.zone} onChange={handleInputChange} />
        </label>
        <label>
          LFG:
          <input type="checkbox" name="lfg" checked={form.lfg} onChange={handleInputChange} />
        </label>
      </div>

      <button onClick={handleSearch}>Search</button>

      <table>
        <thead>
          <tr>
            <th>Level</th>
            <th>Class</th>
            <th>Name</th>
            <th>Race</th>
            <th>Zone</th>
            <th>Guild</th>
            <th>LFG</th>
            <th>Last Updated</th>
          </tr>
        </thead>
          <tbody>
            {data.map((player, index) => (
              <tr key={index}>
                <td>{player.level}</td>
                <td>{player.class}</td>
                <td>{player.name}</td>
                <td>{player.race}</td>
                <td>{player.zone}</td>
                <td>{player.guild}</td>
                <td>{player.lfg ? "Yes" : "No"}</td>
                <td>{new Date(player.last_updated).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
      </table>
    </div>
  );
}

export default App;