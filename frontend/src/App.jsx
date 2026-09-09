import { useState, useEffect, useCallback } from 'react';
import {
  fetchFloodData,
  fetchRainfallData,
  fetchTerrainData,
  fetchRunoffData,
  fetchDrainageData,
  fetchMLStatus,
  fetchMLPredict,
  fetchExplanations,
  fetchPriorities,
  fetchPropagation
} from './services/api';
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

  const [rainfallData, setRainfallData] = useState(null);
  const [terrainData, setTerrainData] = useState(null);
  const [runoffData, setRunoffData] = useState(null);
  const [drainageData, setDrainageData] = useState(null);
  const [mlStatusData, setMlStatusData] = useState(null);
  const [mlPredictData, setMlPredictData] = useState(null);
  const [explanationsData, setExplanationsData] = useState(null);
  const [prioritiesData, setPrioritiesData] = useState(null);
  const [propagationData, setPropagationData] = useState(null);

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
    const [floodRes, rainRes, terrainRes, runoffRes, drainageRes, mlStatRes, mlPredRes, expRes, prioRes, propRes] = await Promise.all([
      fetchFloodData(),
      fetchRainfallData(),
      fetchTerrainData(),
      fetchRunoffData(),
      fetchDrainageData(),
      fetchMLStatus(),
      fetchMLPredict(),
      fetchExplanations(),
      fetchPriorities(),
      fetchPropagation()
    ]);

    setFloodState({
      data: floodRes.data,
      isLive: floodRes.isLive,
      loading: false,
      error: floodRes.error,
      lastSyncTimestamp: floodRes.lastSyncTimestamp
    });

    if (rainRes.data) setRainfallData(rainRes.data);
    if (terrainRes.data) setTerrainData(terrainRes.data);
    if (runoffRes.data) setRunoffData(runoffRes.data);
    if (drainageRes.data) setDrainageData(drainageRes.data);
    if (mlStatRes.data) setMlStatusData(mlStatRes.data);
    if (mlPredRes.data) setMlPredictData(mlPredRes.data);
    if (expRes.data) setExplanationsData(expRes.data);
    if (prioRes.data) setPrioritiesData(prioRes.data);
    if (propRes.data) setPropagationData(propRes.data);
  }, []);

  useEffect(() => {
    let active = true;

    async function initFetch() {
      const [floodRes, rainRes, terrainRes, runoffRes, drainageRes, mlStatRes, mlPredRes, expRes, prioRes, propRes] = await Promise.all([
        fetchFloodData(),
        fetchRainfallData(),
        fetchTerrainData(),
        fetchRunoffData(),
        fetchDrainageData(),
        fetchMLStatus(),
        fetchMLPredict(),
        fetchExplanations(),
        fetchPriorities(),
        fetchPropagation()
      ]);

      if (active) {
        setFloodState({
          data: floodRes.data,
          isLive: floodRes.isLive,
          loading: false,
          error: floodRes.error,
          lastSyncTimestamp: floodRes.lastSyncTimestamp
        });

        if (rainRes.data) setRainfallData(rainRes.data);
        if (terrainRes.data) setTerrainData(terrainRes.data);
        if (runoffRes.data) setRunoffData(runoffRes.data);
        if (drainageRes.data) setDrainageData(drainageRes.data);
        if (mlStatRes.data) setMlStatusData(mlStatRes.data);
        if (mlPredRes.data) setMlPredictData(mlPredRes.data);
        if (expRes.data) setExplanationsData(expRes.data);
        if (prioRes.data) setPrioritiesData(prioRes.data);
        if (propRes.data) setPropagationData(propRes.data);
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
      rainfallData={rainfallData}
      terrainData={terrainData}
      runoffData={runoffData}
      drainageData={drainageData}
      mlStatusData={mlStatusData}
      mlPredictData={mlPredictData}
      explanationsData={explanationsData}
      prioritiesData={prioritiesData}
      propagationData={propagationData}
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
