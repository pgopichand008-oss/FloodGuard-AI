import { useState, useEffect, useCallback } from 'react';
import { fetchFloodData } from './services/api';
import AppShell from './components/AppShell';
import './App.css';

function App() {
  const [floodState, setFloodState] = useState({
    data: null,
    isLive: false,
    loading: true,
    error: null,
    lastSyncTimestamp: null
  });

  const [activeWorkspace, setActiveWorkspace] = useState(null); // null, 'layers', 'forecast', 'drainage', 'analysis', 'routing', 'whatif', 'alerts'
  const [selectedObject, setSelectedObject] = useState(null); // null or { type, id, name }
  const [selectedTimeIndex, setSelectedTimeIndex] = useState(4); // Default +120m peak

  const [layers, setLayers] = useState({
    rainfall: true,
    floodDepth: true,
    dem: false,
    surfaceFlow: true,
    drainageNetwork: true,
    roads: true,
    riskZones: true,
    criticalFacilities: true
  });

  const handleToggleLayer = (key) => {
    setLayers(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleFetch = useCallback(async () => {
    const result = await fetchFloodData();
    setFloodState({
      data: result.data,
      isLive: result.isLive,
      loading: false,
      error: result.error,
      lastSyncTimestamp: result.lastSyncTimestamp
    });
  }, []);

  useEffect(() => {
    let active = true;

    async function initFetch() {
      const result = await fetchFloodData();
      if (active) {
        setFloodState({
          data: result.data,
          isLive: result.isLive,
          loading: false,
          error: result.error,
          lastSyncTimestamp: result.lastSyncTimestamp
        });
      }
    }

    initFetch();
    const interval = setInterval(initFetch, 15000);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <AppShell
      floodState={floodState}
      onRefresh={handleFetch}
      activeWorkspace={activeWorkspace}
      setActiveWorkspace={setActiveWorkspace}
      selectedObject={selectedObject}
      setSelectedObject={setSelectedObject}
      selectedTimeIndex={selectedTimeIndex}
      setSelectedTimeIndex={setSelectedTimeIndex}
      layers={layers}
      onToggleLayer={handleToggleLayer}
    />
  );
}

export default App;
