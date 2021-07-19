import StopsDropdown from "../../components/StopsDropdown"
import RoutesDropdown from "../../components/RoutesDropdown"
import GoogleMap from "../../components/GoogleMap"

function RealtimeTab() {
  const content = {
    display: "grid",
    margin: "5rem 3rem",
    gridTemplateColumns: "1fr 2fr"
  };
  const dropdownsContainer = {
    background: "lightgrey",
    gridColumnStart: "1",
    gridColumnEnd: "2",
    margin: "0 0 0 3rem",
    display: "grid",
    gridTemplateRows: "1fr 1fr"
  };
  const userdropdownContainer  = {
    margin: "3rem"
  };
  const stopdropdownContainer  = {
    margin: "3rem"
  };
  const mapContainer = {
    background: "lightgrey",
    gridColumnStart: "2",
    gridColumnEnd: "3",
    margin: "0 3rem"
  };
  return(
    <div>
      <div style={content}>
        <div style={dropdownsContainer}>
          <div style={userdropdownContainer}>
            <StopsDropdown />
          </div>
          <div style={stopdropdownContainer}>
            <RoutesDropdown />
          </div>
        </div>
        <div style={mapContainer}>
          <GoogleMap />
        </div>
      </div>
    </div>
  )
}

export default RealtimeTab;