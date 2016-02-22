/*

    Script used to calculate overpasses

    Takes an of locations csv and swath csv
*/
#define _USE_MATH_DEFINES

#include <iostream>
#include <iterator>
#include <sstream>
#include <vector>
#include <fstream>
#include <cmath>

using namespace std;

// Define some consts
const double R_earth = 6378137.0; // earth radius [m]

/*
    Store the swaths in a more convenient structure..
*/
struct swath 
{
    int orbit_id;
    vector<long> utc;
    vector<double> grLongitude;
    vector<double> grLatitude;
    vector<double> swWidth;
};

vector<swath>  convert_to_swaths(vector< vector<double> >  &swaths2D) {
    /*
    Convert into a easier structure
    
    Approach:
    want to collect all rows and store into a struct
    until the id changes...
    */

    /*
    1. Count number of seperate swaths and store lenghts of each...
    */
    std::vector<swath> allSwaths;

    int id = 0;
    std::vector<int> id_counts;
    int entry_id=0;
    int id_number_elements = 0;
    // loop over each swath
    for (int i=0; i < swaths2D.size(); i++) {
        id_number_elements++;
        entry_id = swaths2D[i][3];
        if (id != entry_id) 
        {
            id++;
            id_counts.push_back(id_number_elements);
            // reset to zero
            id_number_elements = 0;
        }
    }
    int offset = 0;
    // make swaths
    for (int i=0; i<id; i++) {
        /*
        Create a swath...
        */
        swath aSwath = swath();
        aSwath.orbit_id = i;
        /*
        Collect the data...
        */ 
        int utc;
        double Longitude;
        double Latitude;
        double swathWidth;
        int number_of_entries = id_counts[i];
        for (int rec=0; rec < number_of_entries; rec++) {
            // collect entries
            utc = swaths2D[offset][0];
            Latitude = swaths2D[offset][1];
            Longitude = swaths2D[offset][2];
            swathWidth = swaths2D[offset][4];
            // add to the struct vectors...
            aSwath.utc.push_back(utc);
            aSwath.grLatitude.push_back(Latitude);
            aSwath.grLongitude.push_back(Longitude);
            aSwath.swWidth.push_back(swathWidth);
            // add one to offset
            offset++;
        }
        // add this swath to the swaths vec
        allSwaths.push_back(aSwath);
    }
    return allSwaths;
}



/*
    File loading stuff
    ==================
*/
vector< vector<double> > load_swath_file(string filename) {
    // Set up storage vector
    vector< vector<double> > swStore;
    vector<double> swRow;
    // load file
    ifstream stream(filename);
    // file elements
    string line;
    string item;
    // loop over lines
    for (string line; getline(stream, line); )
    {
        istringstream ln(line);
        while (getline(ln, item, ','))
        {
            // get item in row
            swRow.push_back(atof(item.c_str()));
        }
        swStore.push_back(swRow);
        swRow.clear();
    }
    return swStore;
}

vector< vector<double> > load_pixels_file(string filename) 
{
    // Set up storage vector
    vector< vector<double> > swStore;
    vector<double> swRow;
    // load file
    ifstream stream(filename);
    // file elements
    string line;
    string item;
    // loop over lines
    for (string line; getline(stream, line); ) 
    {
        istringstream ln(line);
        while (getline(ln, item, ','))
         { 
            // get field in line
            swRow.push_back(atof(item.c_str())); 
        }
        swStore.push_back(swRow);
        swRow.clear();
    }
    return swStore;
}


/*
    Geodetic
    ========
*/

double haversine(double lat1, double lon1, double lat2, double lon2) {
    /*
    Haversine implementation to get distance between
    two locations in metres
    */
    // convert to radians
    lon1 = lon1 * (M_PI / 180.0); 
    lat1 = lat1 * (M_PI / 180.0); 
    lon2 = lon2 * (M_PI / 180.0); 
    lat2 = lat2 * (M_PI / 180.0); 
    // haversine formula 
    double dlon = lon2 - lon1;
    double dlat = lat2 - lat1;
    double a = pow(sin(dlat/2.0),2.0) + cos(lat1) * cos(lat2) * pow(sin(dlon/2.0),2.0);
    double c = 2 * asin(sqrt(a));
    double dist = c * R_earth;
    return dist;
}

double latitudeDistance(double lat0, double lat1) {
    // compute distance between two latitudes
    double dlat = abs(lat1 - lat0);
    double distance  = pow((lat1 - lat0),2.0);
    return distance;

}


int count_overpasses(double lat, double lon, std::vector<swath> &swaths ) {
    /*
        Calculate the number of overpasses for a location
    */
    int counts = 0;

    /* iterate through the swaths and find:
        1. nearest latitude location
        2. Whether the coord at [1.] is within 0.5 * swathWidth or this earthPoint.
    */

    std::vector<swath>::iterator sw;
    for (sw = swaths.begin(); sw != swaths.end(); ++sw) {
        /*
        Iterate through all the latitudes of the swath to find the nearest
        */
        int min_latitude_idx = 0;
        double dist = 0;
        double mindist = 1e12;
        int idx = 0;
        // loop over all latitudes in swath
        for (int j=0; j <  sw->grLatitude.size(); j++)
        {
            /*
                Find index of nearest latitude 
            */
            double orbitLat = sw->grLatitude[j];
            dist = latitudeDistance( lat, orbitLat );
            //cout << dist << endl;
            if (dist < mindist) 
            {
                // set min distance and set right latitude index...
                mindist = dist;
                min_latitude_idx = idx;
            }
            // increment index counter
            idx++;
        }
        /*
        Now have the minimum distance latitude location for this orbit
        Want to check whether this location to our point is within 0.5* swathWidth
        */
        //cout << "min index is: " << min_latitude_idx << endl;
        double orbitLatitude =  sw->grLatitude[min_latitude_idx];
        double orbitLongitude = sw->grLongitude[min_latitude_idx];
        /*
        Perform distance calculation
        */
        double distance;
        distance = haversine(lat, lon, orbitLatitude, orbitLongitude);
        //cout <<  "Metres distance between locations (" << lat << ", " << lon << ") and (" << orbitLatitude << "," << orbitLongitude << ") is: " << distance << endl;
        //cout << sw->orbit_id << " " << min_latitude_idx << " " << mindist << endl; 
        /*
        Check whether this distance is less than 0.5 swath
        */
        if (distance < 0.5 * sw->swWidth[min_latitude_idx]) {
            // add one to count
            counts++;
        }
    }
    return counts;
}

/*
    Main
    ====
*/

int main(int argc, char* argv[]) {
    
    if (argc != 3) {
        std::cerr << "* Count Overpasses *\n\n" 
                  << "Program which counts satellite overpasses for location.\n"
                  << "Outputs location and counts.\n\n"
                  << "Usage: " << argv[0] << " [ orbits_file ]" 
                  << " [ ground_locations_file ]"<< " > [ counts_file ] "<< std::endl;
        return(1);
    }
    // associate command line args with files
    string swathFile = argv[1];
    string coordinates = argv[2];

    // Load swath data file
    vector< vector<double> > swaths_f = load_swath_file(swathFile);

    // put into structures
    vector<swath> swaths = convert_to_swaths(swaths_f);  

    // Load the pixel locations
    vector< vector<double> > locations = load_pixels_file(coordinates);
  
    /*
    Do counts
    */
    double lat;
    double lon;
    double land;
    int count;
    double fill = -999.0;
    for (int i=0; i < locations.size(); i++) {
        /*
        Iterate through and do counts
        */
        lat = locations[i][0];
        lon = locations[i][1];
        land = locations[i][2];
        if (land == 1.0) {
            count =  count_overpasses(lat, lon, swaths);
            cout << lat << " " << lon <<  " "<<count << endl;
        }
        else {
            // is water so put a fill value
            cout << lat << " " << lon <<  " "<< fill << endl;
        }
    } 
}
