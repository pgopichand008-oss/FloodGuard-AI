import React from 'react';

export default function MapCompass({ onResetView }) {
  return (
    <button
      type="button"
      className="map-compass-ring-btn"
      onClick={onResetView}
      title="North, West, South, East Orientation Compass — Click to reset map orientation & home view"
      aria-label="Compass - Reset orientation to North"
    >
      <span className="compass-dir compass-dir-n">N</span>
      <span className="compass-dir compass-dir-s">S</span>
      <span className="compass-dir compass-dir-w">W</span>
      <span className="compass-dir compass-dir-e">E</span>
      <div className="compass-center-arrow" aria-hidden="true">▲</div>
    </button>
  );
}
