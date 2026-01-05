import React, { useState, useEffect, useContext, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api, AuthContext } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ArrowLeft, User, MapPin, Compass, FileText, Clock, AlertCircle, Search, Globe, Building, Home } from 'lucide-react';

const RADIUS_OPTIONS = [3, 5, 10];

// City search component with typeahead
const CitySearch = ({ country, onSelect, value }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const { t } = useTranslation();

  const searchCities = useCallback(async (searchQuery) => {
    if (searchQuery.length < 2) {
      setResults([]);
      return;
    }
    
    setLoading(true);
    try {
      const response = await api.get(`/locations/search?query=${encodeURIComponent(searchQuery)}&country=${country || ''}`);
      setResults(response.data);
      setShowDropdown(true);
    } catch (error) {
      console.error('Failed to search cities:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [country]);

  useEffect(() => {
    const debounce = setTimeout(() => {
      searchCities(query);
    }, 300);
    return () => clearTimeout(debounce);
  }, [query, searchCities]);

  const handleSelect = (place) => {
    onSelect(place);
    setQuery(place.label);
    setShowDropdown(false);
    setResults([]);
  };

  return (
    <div className="relative">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder={t('profile.searchCity')}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setShowDropdown(true)}
          className="pl-10"
        />
        {loading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
          </div>
        )}
      </div>
      
      {showDropdown && results.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-background border rounded-md shadow-lg max-h-60 overflow-auto">
          {results.map((place) => (
            <button
              key={place.place_id}
              onClick={() => handleSelect(place)}
              className="w-full px-4 py-3 text-left hover:bg-muted flex items-center gap-3 border-b last:border-b-0"
            >
              <MapPin className="h-4 w-4 text-muted-foreground flex-shrink-0" />
              <div>
                <p className="font-medium">{place.city_name}</p>
                <p className="text-sm text-muted-foreground">{place.region_name}, {place.country_code}</p>
              </div>
            </button>
          ))}
        </div>
      )}
      
      {value && (
        <p className="mt-2 text-sm text-muted-foreground flex items-center gap-2">
          <MapPin className="h-4 w-4" />
          {value.label}
        </p>
      )}
    </div>
  );
};

export const Profile = () => {
  const [displayName, setDisplayName] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [locationStatus, setLocationStatus] = useState(null);
  const [showLocationDialog, setShowLocationDialog] = useState(false);
  const [showRadiusDialog, setShowRadiusDialog] = useState(false);
  const [termsStatus, setTermsStatus] = useState(null);
  
  // Location form state
  const [countries, setCountries] = useState([]);
  const [selectedCountry, setSelectedCountry] = useState('');
  const [selectedPlace, setSelectedPlace] = useState(null);
  const [neighborhood, setNeighborhood] = useState('');
  const [selectedRadius, setSelectedRadius] = useState(5);
  const [updatingLocation, setUpdatingLocation] = useState(false);
  const [updatingRadius, setUpdatingRadius] = useState(false);
  
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const { user, login } = useContext(AuthContext);

  useEffect(() => {
    fetchProfile();
    fetchLocationStatus();
    fetchTermsStatus();
    fetchCountries();
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await api.get('/auth/me');
      setDisplayName(response.data.display_name || '');
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const fetchLocationStatus = async () => {
    try {
      const response = await api.get('/me/location-status');
      setLocationStatus(response.data);
      setSelectedRadius(response.data.radius?.km || 5);
      
      // Pre-fill country if location exists
      if (response.data.location?.country_code) {
        setSelectedCountry(response.data.location.country_code);
      }
      if (response.data.location?.neighborhood_text) {
        setNeighborhood(response.data.location.neighborhood_text);
      }
    } catch (error) {
      console.error('Failed to fetch location status:', error);
    }
  };

  const fetchTermsStatus = async () => {
    try {
      const response = await api.get('/user/terms-status');
      setTermsStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch terms status:', error);
    }
  };

  const fetchCountries = async () => {
    try {
      const response = await api.get(`/locations/countries?language=${i18n.language}`);
      setCountries(response.data);
    } catch (error) {
      console.error('Failed to fetch countries:', error);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const response = await api.patch('/auth/me', {
        display_name: displayName.trim() || null
      });
      
      const token = localStorage.getItem('token');
      login(token, response.data);
      
      toast.success(t('profile.saved'));
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateLocation = async () => {
    if (!selectedPlace) {
      toast.error(t('profile.selectCity'));
      return;
    }
    
    setUpdatingLocation(true);
    try {
      await api.post('/me/location', {
        country_code: selectedPlace.country_code,
        region_name: selectedPlace.region_name,
        city_name: selectedPlace.city_name,
        place_id: selectedPlace.place_id,
        latitude: selectedPlace.latitude,
        longitude: selectedPlace.longitude,
        neighborhood_text: neighborhood.trim() || null,
        radius_km: selectedRadius
      });
      
      toast.success(t('profile.locationUpdated'));
      setShowLocationDialog(false);
      fetchLocationStatus();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setUpdatingLocation(false);
    }
  };

  const handleUpdateRadius = async () => {
    setUpdatingRadius(true);
    try {
      await api.put('/me/radius', {
        radius_km: selectedRadius
      });
      
      toast.success(t('profile.radiusUpdated'));
      setShowRadiusDialog(false);
      fetchLocationStatus();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setUpdatingRadius(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-2xl font-bold">{t('common.loading')}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen sticker-album-pattern">
      <div className="max-w-2xl mx-auto p-6">
        <div className="flex items-center gap-4 mb-8">
          <Button
            data-testid="back-btn"
            variant="outline"
            size="icon"
            onClick={() => navigate('/settings')}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-3xl font-black tracking-tight text-primary">{t('profile.title')}</h1>
        </div>

        {/* Location Setup Required Warning */}
        {locationStatus?.needs_location_setup && (
          <Card className="mb-6 border-amber-300 bg-amber-50">
            <CardContent className="p-4 flex items-start gap-3">
              <AlertCircle className="h-6 w-6 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-amber-800">{t('profile.locationRequired')}</p>
                <p className="text-sm text-amber-700 mt-1">{t('profile.locationRequiredDesc')}</p>
                <Button
                  onClick={() => setShowLocationDialog(true)}
                  className="mt-3"
                  size="sm"
                >
                  {t('profile.setLocation')}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Basic Profile Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              {t('profile.basicInfo')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSave} className="space-y-4">
              <div>
                <Label htmlFor="displayName">{t('profile.displayName')}</Label>
                <Input
                  id="displayName"
                  data-testid="display-name-input"
                  type="text"
                  placeholder={t('profile.displayNamePlaceholder')}
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  maxLength={50}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  {t('profile.helperText')}
                </p>
              </div>

              <div>
                <Label>{t('profile.email')}</Label>
                <Input
                  type="email"
                  value={user?.email}
                  disabled
                  className="bg-muted"
                />
              </div>

              <Button
                data-testid="save-profile-btn"
                type="submit"
                className="w-full btn-primary"
                disabled={saving}
              >
                {saving ? t('common.loading') : t('profile.save')}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Location & Radius Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MapPin className="h-5 w-5" />
              {t('profile.locationTitle')}
            </CardTitle>
            <CardDescription>
              {t('profile.locationDescription')}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Location Display */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="flex items-center gap-2">
                  <Globe className="h-4 w-4" />
                  {t('profile.location')}
                </Label>
                {locationStatus?.location?.can_change ? (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowLocationDialog(true)}
                  >
                    {locationStatus?.has_location ? t('profile.changeLocation') : t('profile.setLocation')}
                  </Button>
                ) : (
                  <Badge variant="secondary" className="flex items-center gap-1 text-xs">
                    <Clock className="h-3 w-3" />
                    {t('profile.locationCooldown', { days: locationStatus?.location?.days_until_change || 0 })}
                  </Badge>
                )}
              </div>
              <div className="bg-muted rounded-lg p-4 space-y-2">
                {locationStatus?.has_location ? (
                  <>
                    <div className="flex items-center gap-2">
                      <Building className="h-4 w-4 text-primary" />
                      <span className="font-medium">{locationStatus.location.label}</span>
                    </div>
                    {locationStatus.location.neighborhood_text && (
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Home className="h-4 w-4" />
                        <span>{locationStatus.location.neighborhood_text}</span>
                      </div>
                    )}
                  </>
                ) : (
                  <p className="text-muted-foreground italic">{t('profile.noLocationSet')}</p>
                )}
              </div>
            </div>

            {/* Search Radius */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="flex items-center gap-2">
                  <Compass className="h-4 w-4" />
                  {t('profile.searchRadius')}
                </Label>
                {locationStatus?.radius?.can_change ? (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowRadiusDialog(true)}
                  >
                    {t('profile.changeRadius')}
                  </Button>
                ) : (
                  <Badge variant="secondary" className="flex items-center gap-1 text-xs">
                    <Clock className="h-3 w-3" />
                    {t('profile.radiusCooldown', { days: locationStatus?.radius?.days_until_change || 0 })}
                  </Badge>
                )}
              </div>
              <div className="bg-muted rounded-lg p-4">
                <p className="font-medium flex items-center gap-2">
                  <Compass className="h-4 w-4 text-primary" />
                  {locationStatus?.radius?.km || 5} km
                </p>
              </div>
            </div>

            {/* Privacy Note */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex gap-2">
              <AlertCircle className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-blue-800">
                {t('profile.locationPrivacyNote')}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Terms & Conditions Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              {t('profile.termsTitle')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {termsStatus?.terms_accepted && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <p className="text-sm text-green-800 font-medium mb-2">
                    {t('profile.termsAccepted')}
                  </p>
                  <div className="text-xs text-green-700 space-y-1">
                    <p>{t('profile.termsVersion')}: {termsStatus.terms_version}</p>
                    <p>{t('profile.termsAcceptedAt')}: {new Date(termsStatus.terms_accepted_at).toLocaleDateString()}</p>
                  </div>
                </div>
              )}
              <Button
                variant="outline"
                className="w-full"
                onClick={() => navigate('/terms')}
              >
                {t('profile.viewTerms')}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Location Setup Dialog */}
        <Dialog open={showLocationDialog} onOpenChange={setShowLocationDialog}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>{t('profile.setupLocation')}</DialogTitle>
              <DialogDescription>
                {t('profile.setupLocationDesc')}
              </DialogDescription>
            </DialogHeader>
            <div className="py-4 space-y-6">
              {/* Country Selection */}
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <Globe className="h-4 w-4" />
                  {t('profile.country')} *
                </Label>
                <Select value={selectedCountry} onValueChange={(value) => {
                  setSelectedCountry(value);
                  setSelectedPlace(null);
                }}>
                  <SelectTrigger>
                    <SelectValue placeholder={t('profile.selectCountry')} />
                  </SelectTrigger>
                  <SelectContent className="max-h-60">
                    {countries.map((country) => (
                      <SelectItem key={country.code} value={country.code}>
                        {country.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* City Search */}
              {selectedCountry && (
                <div className="space-y-2">
                  <Label className="flex items-center gap-2">
                    <Building className="h-4 w-4" />
                    {t('profile.city')} *
                  </Label>
                  <CitySearch
                    country={selectedCountry}
                    onSelect={setSelectedPlace}
                    value={selectedPlace}
                  />
                  <p className="text-xs text-muted-foreground">
                    {t('profile.citySearchHelp')}
                  </p>
                </div>
              )}

              {/* Neighborhood (Optional) */}
              {selectedPlace && (
                <div className="space-y-2">
                  <Label className="flex items-center gap-2">
                    <Home className="h-4 w-4" />
                    {t('profile.neighborhood')} ({t('common.optional')})
                  </Label>
                  <Input
                    placeholder={t('profile.neighborhoodPlaceholder')}
                    value={neighborhood}
                    onChange={(e) => setNeighborhood(e.target.value)}
                    maxLength={100}
                  />
                  <p className="text-xs text-muted-foreground">
                    {t('profile.neighborhoodHelp')}
                  </p>
                </div>
              )}

              {/* Search Radius */}
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <Compass className="h-4 w-4" />
                  {t('profile.searchRadius')}
                </Label>
                <div className="grid grid-cols-3 gap-2">
                  {RADIUS_OPTIONS.map((radius) => (
                    <Button
                      key={radius}
                      type="button"
                      variant={selectedRadius === radius ? 'default' : 'outline'}
                      onClick={() => setSelectedRadius(radius)}
                      className="w-full"
                    >
                      {radius} km
                    </Button>
                  ))}
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowLocationDialog(false)}>
                {t('common.cancel')}
              </Button>
              <Button
                onClick={handleUpdateLocation}
                disabled={updatingLocation || !selectedPlace}
              >
                {updatingLocation ? t('common.loading') : t('common.save')}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Radius Change Dialog */}
        <Dialog open={showRadiusDialog} onOpenChange={setShowRadiusDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{t('profile.changeRadius')}</DialogTitle>
              <DialogDescription>
                {t('profile.changeRadiusDescription')}
              </DialogDescription>
            </DialogHeader>
            <div className="py-4">
              <Label>{t('profile.selectRadius')}</Label>
              <div className="grid grid-cols-3 gap-2 mt-2">
                {RADIUS_OPTIONS.map((radius) => (
                  <Button
                    key={radius}
                    variant={selectedRadius === radius ? 'default' : 'outline'}
                    onClick={() => setSelectedRadius(radius)}
                    className="w-full"
                  >
                    {radius} km
                  </Button>
                ))}
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowRadiusDialog(false)}>
                {t('common.cancel')}
              </Button>
              <Button onClick={handleUpdateRadius} disabled={updatingRadius}>
                {updatingRadius ? t('common.loading') : t('common.save')}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default Profile;
