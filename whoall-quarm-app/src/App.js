import React, {useState, useEffect} from 'react';
import Select from 'react-select';
import './App.css';


function App() {
    const [darkMode, setDarkMode] = useState(true);
    const [lastUpdatedDate, setLastUpdatedDate] = useState(null);
    const [data, setData] = useState([]);
    const [searchResults, setSearchResults] = useState([]);
    const [loading, setLoading] = useState(true);
    const [sort, setSort] = useState({column: 'level', direction: 'asc'});
    const [manifest, setManifest] = useState([]);
    const [selectedDataFile, setSelectedDataFile] = useState(null);
    const [form, setForm] = useState({
        level_start: '',
        level_end: '',
        class_: '',
        name: '',
        race: '',
        guild: '',
        zone: '',
        lfg: false,
        last_updated: ''
    });

    const customStyles = darkMode => ({
        control: (provided) => ({
            ...provided,
            backgroundColor: darkMode ? '#2E2E2E' : 'white',
            borderColor: darkMode ? '#555555' : provided.borderColor,
            color: darkMode ? 'white' : 'black',
        }),
        option: (provided) => ({
            ...provided,
            backgroundColor: darkMode ? '#2E2E2E' : 'white',
            color: darkMode ? 'white' : 'black',
        }),
        singleValue: (provided) => ({
            ...provided,
            color: darkMode ? 'white' : 'black',
            marginLeft: '50%',
            transform: 'translateX(-50%)'
        }),
        input: (provided, state) => {
            const length = state.selectProps.inputValue?.length || 0;
            const paddingAmount = Math.max(0, 50 - (length*0.2)); // Adjust as needed

            return {
                ...provided,
                paddingLeft: `${paddingAmount}%`,
                color: darkMode ? 'white' : 'black'
            };
        },
        placeholder: (provided) => ({
            ...provided,
            color: darkMode ? '#aaa' : '#666',
            marginLeft: '50%',
            transform: 'translateX(-50%)'
        }),
        noOptionsMessage: (provided) => ({
            ...provided,
            color: darkMode ? 'white' : 'black',
            backgroundColor: darkMode ? '#2E2E2E' : 'white'
        }),
        dropdownIndicator: (provided) => ({
            ...provided,
            color: darkMode ? 'white' : 'black'
        }),
        clearIndicator: (provided) => ({
            ...provided,
            color: darkMode ? 'white' : 'black'
        }),
        multiValue: (provided) => ({
            ...provided,
            backgroundColor: darkMode ? '#555555' : '#ddd'
        }),
        multiValueLabel: (provided) => ({
            ...provided,
            color: darkMode ? 'white' : 'black'
        }),
        multiValueRemove: (provided) => ({
            ...provided,
            color: darkMode ? 'white' : 'black',
            ':hover': {
                backgroundColor: darkMode ? 'red' : '#ddd',
                color: 'white'
            }
        })
    });

    useEffect(() => {
        document.body.classList.toggle('dark-mode', darkMode);
    }, [darkMode]);

    useEffect(() => {
        // Fetch manifest data
        async function fetchManifest() {
            const url = 'https://raw.githubusercontent.com/crdunwel/whoall-quarm/main/data/manifest.json';
            const response = await fetch(url);
            const data = await response.json();

            // Assuming that the last file in the manifest is the latest
            const latest = data.pop();

            // Convert to format suitable for react-select, and label the latest as "Latest"
            setManifest([
                {label: 'Latest', value: latest},
                ...data.map(file => ({label: file, value: file}))
            ]);
        }

        fetchManifest();

        // Set a timer to fetch manifest every 10 minutes (or whatever interval you prefer)
        const manifestIntervalId = setInterval(fetchManifest, 10 * 60 * 1000);

        // Clean up the interval on component unmount
        return () => clearInterval(manifestIntervalId);
    }, []);

    useEffect(() => {
        async function fetchData() {
            const url = 'https://raw.githubusercontent.com/crdunwel/whoall-quarm/main/data.json';
            const response = await fetch(url);
            const jsonData = await response.json();
            setData(jsonData.data);
            setLastUpdatedDate(new Date(jsonData.last_updated * 1000));  // Convert seconds to milliseconds
            setLoading(false);
        }

        fetchData();

        // Set a timer to fetch data every minute
        const intervalId = setInterval(fetchData, 60 * 1000);

        // Clean up the interval on component unmount
        return () => clearInterval(intervalId);

    }, []); // Removed dependency on db

    const toggleDarkMode = () => {
        setDarkMode(!darkMode);
    };

    // Handler when selecting a data file from react-select
    const handleDataFileChange = async (selectedOption) => {
        setSelectedDataFile(selectedOption);
        if (selectedOption && selectedOption.value) {
            const url = `https://raw.githubusercontent.com/crdunwel/whoall-quarm/main/data/${selectedOption.value}`;
            const response = await fetch(url);
            const jsonData = await response.json();
            setData(jsonData.data);
            setLastUpdatedDate(new Date(jsonData.last_updated * 1000));
        }
    }

    const formatFilenameToTimestamp = (filename) => {
        // Extract date and time
        const [date, time] = filename.split('_');

        // Convert the time from H-M-S to H:M:S
        const formattedTime = time.split('-').join(':').replace('.json', '');

        return `${date} ${formattedTime}`;
    };

    const handleSearch = () => {
        let filteredData = [...data];

        if (form.level_start && form.level_end) {
            filteredData = filteredData.filter(player => player.level >= form.level_start && player.level <= form.level_end);
        }
        if (form.class_) {
            filteredData = filteredData.filter(player => player.class.toLowerCase() === form.class_.toLowerCase());
        }
        if (form.name) {
            filteredData = filteredData.filter(player => player.name.toLowerCase().includes(form.name.toLowerCase()));
        }
        if (form.race) {
            filteredData = filteredData.filter(player => player.race.toLowerCase() === form.race.toLowerCase());
        }
        if (form.guild) {
            filteredData = filteredData.filter(player => player.guild.toLowerCase() === form.guild.toLowerCase());
        }
        if (form.zone) {
            filteredData = filteredData.filter(player => player.zone.toLowerCase() === form.zone.toLowerCase());
        }
        if (form.lfg) {
            filteredData = filteredData.filter(player => player.lfg === 1);
        } else {
            filteredData = filteredData.filter(player => player.lfg === 0);
        }
        setSearchResults(filteredData);
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') handleSearch();
    };

    const handleSort = (column) => {
        const newDirection = (sort.column === column && sort.direction === 'asc') ? 'desc' : 'asc';
        const sortedResults = [...searchResults].sort((a, b) => {
            if (a[column] < b[column]) return newDirection === 'asc' ? -1 : 1;
            if (a[column] > b[column]) return newDirection === 'asc' ? 1 : -1;
            return 0;
        });
        setSearchResults(sortedResults);
        setSort({column, direction: newDirection});
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
            <div>
                <Select
                    styles={customStyles(darkMode)}
                    value={selectedDataFile}
                    onChange={handleDataFileChange}
                    options={manifest}
                    isSearchable={true} // This will allow users to search within the dropdown
                    placeholder="Select archived data..."
                    noOptionsMessage={() => "No Results"}
                />
            </div>
            <h1>Quarm Player Query</h1>


            <p>Data last updated: {lastUpdatedDate && lastUpdatedDate.toLocaleString()}</p>

            <button onClick={toggleDarkMode}>
                {darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            </button>

            <div className="form-container">
                {/* Grouped related inputs together for a more intuitive user experience */}
                <div className="input-group">
                    <label>
                        Level Start:
                        <input type="number" name="level_start" value={form.level_start} onChange={handleInputChange}
                               onKeyDown={handleKeyPress}/>
                    </label>
                    <label>
                        Level End:
                        <input type="number" name="level_end" value={form.level_end} onChange={handleInputChange}
                               onKeyDown={handleKeyPress}/>
                    </label>
                </div>

                <div className="input-group">
                    <label>
                        Class:
                        <input type="text" name="class_" value={form.class_} onChange={handleInputChange}
                               onKeyDown={handleKeyPress}/>
                    </label>
                    <label>
                        Race:
                        <input type="text" name="race" value={form.race} onChange={handleInputChange}
                               onKeyDown={handleKeyPress}/>
                    </label>
                </div>

                <div className="input-group">
                    <label>
                        Name:
                        <input type="text" name="name" value={form.name} onChange={handleInputChange}
                               onKeyDown={handleKeyPress}/>
                    </label>
                    <label>
                        Guild:
                        <input type="text" name="guild" value={form.guild} onChange={handleInputChange}
                               onKeyDown={handleKeyPress}/>
                    </label>
                </div>

                <div className="input-group">
                    <label>
                        Zone:
                        <input type="text" name="zone" value={form.zone} onChange={handleInputChange}
                               onKeyDown={handleKeyPress}/>
                    </label>
                    <div className="lfg-container">
                        <label className="lfg-label" htmlFor="lfg-checkbox">LFG:</label>
                        <input type="checkbox" id="lfg-checkbox" name="lfg" checked={form.lfg}
                               onChange={handleInputChange}/>
                        <button onClick={handleSearch} className="submit-button">Search</button>
                    </div>
                </div>

                {/*<div className="submit-button">*/}
                {/*  <button onClick={handleSearch}>Search</button>*/}
                {/*</div>*/}
            </div>
            <p>{searchResults.length} results found.</p>
            <table>
                <thead>
                <tr>
                    <th onClick={() => handleSort('level')}>Level</th>
                    <th onClick={() => handleSort('class')}>Class</th>
                    <th onClick={() => handleSort('name')}>Name</th>
                    <th onClick={() => handleSort('race')}>Race</th>
                    <th onClick={() => handleSort('zone')}>Zone</th>
                    <th onClick={() => handleSort('guild')}>Guild</th>
                    <th onClick={() => handleSort('lfg')}>LFG</th>
                    <th onClick={() => handleSort('last_updated')}>Last Updated</th>
                </tr>
                </thead>
                <tbody>
                {searchResults.map((player, index) => (
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