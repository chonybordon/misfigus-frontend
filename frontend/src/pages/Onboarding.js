import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { User, MapPin, Compass, FileText, Search, ChevronRight } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const RADIUS_OPTIONS = [3, 5, 10, 15, 20];

// City search component with typeahead
const CitySearch = ({ country, onSelect, value, disabled }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const { t } = useTranslation();

  const searchCities = useCallback(async (searchQuery) => {
    if (searchQuery.length < 2 || !country) {
      setResults([]);
      return;
    }
    
    setLoading(true);
    try {
      const response = await api.get(`/locations/search?query=${encodeURIComponent(searchQuery)}&country=${country}`);
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
          placeholder={t('onboarding.searchCity')}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setShowDropdown(true)}
          className="pl-10"
          disabled={disabled || !country}
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
        <p className="mt-2 text-sm text-green-600 flex items-center gap-2">
          <MapPin className="h-4 w-4" />
          {value.label}
        </p>
      )}
      
      {!country && (
        <p className="mt-2 text-sm text-muted-foreground">{t('onboarding.selectCountryFirst')}</p>
      )}
    </div>
  );
};

export const Onboarding = ({ onComplete }) => {
  const [step, setStep] = useState(1);
  const [fullName, setFullName] = useState('');
  const [countries, setCountries] = useState([]);
  const [selectedCountry, setSelectedCountry] = useState('');
  const [selectedPlace, setSelectedPlace] = useState(null);
  const [neighborhood, setNeighborhood] = useState('');
  const [selectedRadius, setSelectedRadius] = useState(5);
  const [termsContent, setTermsContent] = useState('');
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [saving, setSaving] = useState(false);
  const { t, i18n } = useTranslation();

  useEffect(() => {
    fetchCountries();
    fetchTerms();
  }, [i18n.language]);

  const fetchCountries = async () => {
    try {
      const response = await api.get(`/locations/countries?language=${i18n.language}`);
      setCountries(response.data);
    } catch (error) {
      console.error('Failed to fetch countries:', error);
    }
  };

  const fetchTerms = async () => {
    try {
      const response = await api.get(`/terms?language=${i18n.language}`);
      setTermsContent(response.data.content);
    } catch (error) {
      console.error('Failed to fetch terms:', error);
    }
  };

  const canProceedToStep2 = fullName.trim().length >= 2;
  const canProceedToStep3 = selectedPlace !== null;
  const canComplete = termsAccepted;

  const handleComplete = async () => {
    if (!canComplete) return;
    
    setSaving(true);
    try {
      const response = await api.post('/user/complete-onboarding', {
        full_name: fullName.trim(),
        country_code: selectedPlace.country_code,
        region_name: selectedPlace.region_name,
        city_name: selectedPlace.city_name,
        place_id: selectedPlace.place_id,
        latitude: selectedPlace.latitude,
        longitude: selectedPlace.longitude,
        neighborhood_text: neighborhood.trim() || null,
        radius_km: selectedRadius,
        terms_version: '1.0'
      });
      
      // Update cached user data
      const updatedUser = response.data.user;
      localStorage.setItem('user', JSON.stringify(updatedUser));
      
      toast.success(t('onboarding.success'));
      onComplete(updatedUser);
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setSaving(false);
    }
  };

  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <div className="mx-auto h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
          <User className="h-8 w-8 text-primary" />
        </div>
        <h2 className="text-xl font-bold">{t('onboarding.step1Title')}</h2>
        <p className="text-muted-foreground text-sm">{t('onboarding.step1Subtitle')}</p>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="fullName">{t('onboarding.fullName')} *</Label>
        <Input
          id="fullName"
          type="text"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          placeholder={t('onboarding.fullNamePlaceholder')}
          autoFocus
          maxLength={100}
        />
        <p className="text-xs text-muted-foreground">{t('onboarding.fullNameHelp')}</p>
      </div>
      
      <Button
        onClick={() => setStep(2)}
        disabled={!canProceedToStep2}
        className="w-full"
      >
        {t('onboarding.continue')}
        <ChevronRight className="h-4 w-4 ml-2" />
      </Button>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <div className="mx-auto h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
          <MapPin className="h-8 w-8 text-primary" />
        </div>
        <h2 className="text-xl font-bold">{t('onboarding.step2Title')}</h2>
        <p className="text-muted-foreground text-sm">{t('onboarding.step2Subtitle')}</p>
      </div>
      
      {/* Country Selection */}
      <div className="space-y-2">
        <Label>{t('onboarding.country')} *</Label>
        <Select value={selectedCountry} onValueChange={(value) => {
          setSelectedCountry(value);
          setSelectedPlace(null); // Reset city when country changes
        }}>
          <SelectTrigger>
            <SelectValue placeholder={t('onboarding.selectCountry')} />
          </SelectTrigger>
          <SelectContent>
            {countries.map((country) => (
              <SelectItem key={country.code} value={country.code}>
                {country.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      
      {/* City Search */}
      <div className="space-y-2">
        <Label>{t('onboarding.city')} *</Label>
        <CitySearch
          country={selectedCountry}
          onSelect={setSelectedPlace}
          value={selectedPlace}
        />
      </div>
      
      {/* Neighborhood (Optional) */}
      <div className="space-y-2">
        <Label>{t('onboarding.neighborhood')} <span className="text-muted-foreground">({t('common.optional')})</span></Label>
        <Input
          value={neighborhood}
          onChange={(e) => setNeighborhood(e.target.value)}
          placeholder={t('onboarding.neighborhoodPlaceholder')}
          maxLength={100}
        />
      </div>
      
      {/* Radius Selection */}
      <div className="space-y-2">
        <Label className="flex items-center gap-2">
          <Compass className="h-4 w-4" />
          {t('onboarding.searchRadius')} *
        </Label>
        <Select value={selectedRadius.toString()} onValueChange={(value) => setSelectedRadius(parseInt(value))}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {RADIUS_OPTIONS.map((radius) => (
              <SelectItem key={radius} value={radius.toString()}>
                {radius} km
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <p className="text-xs text-muted-foreground">{t('onboarding.radiusHelp')}</p>
      </div>
      
      <div className="flex gap-2">
        <Button variant="outline" onClick={() => setStep(1)} className="flex-1">
          {t('common.back')}
        </Button>
        <Button
          onClick={() => setStep(3)}
          disabled={!canProceedToStep3}
          className="flex-1"
        >
          {t('onboarding.continue')}
          <ChevronRight className="h-4 w-4 ml-2" />
        </Button>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6">
      <div className="text-center mb-4">
        <div className="mx-auto h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
          <FileText className="h-8 w-8 text-primary" />
        </div>
        <h2 className="text-xl font-bold">{t('onboarding.step3Title')}</h2>
        <p className="text-muted-foreground text-sm">{t('onboarding.step3Subtitle')}</p>
      </div>
      
      {/* Terms Content */}
      <Card className="border-2">
        <ScrollArea className="h-[250px] p-4">
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown>{termsContent}</ReactMarkdown>
          </div>
        </ScrollArea>
      </Card>
      
      {/* Terms Checkbox */}
      <div className="flex items-start space-x-3 p-4 bg-muted rounded-lg">
        <Checkbox
          id="terms"
          checked={termsAccepted}
          onCheckedChange={setTermsAccepted}
          className="mt-1"
        />
        <label
          htmlFor="terms"
          className="text-sm font-medium leading-relaxed cursor-pointer"
        >
          {t('onboarding.acceptTerms')} *
        </label>
      </div>
      
      <div className="flex gap-2">
        <Button variant="outline" onClick={() => setStep(2)} className="flex-1">
          {t('common.back')}
        </Button>
        <Button
          onClick={handleComplete}
          disabled={!canComplete || saving}
          className="flex-1 btn-primary"
        >
          {saving ? t('common.loading') : t('onboarding.complete')}
        </Button>
      </div>
    </div>
  );

  // Progress indicator
  const renderProgress = () => (
    <div className="flex justify-center gap-2 mb-6">
      {[1, 2, 3].map((s) => (
        <div
          key={s}
          className={`h-2 w-16 rounded-full transition-colors ${
            s <= step ? 'bg-primary' : 'bg-muted'
          }`}
        />
      ))}
    </div>
  );

  return (
    <div className="min-h-screen sticker-album-pattern flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="pb-2">
          <CardTitle className="text-center text-2xl font-black text-primary">
            {t('onboarding.title')}
          </CardTitle>
          <CardDescription className="text-center">
            {t('onboarding.subtitle')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {renderProgress()}
          {step === 1 && renderStep1()}
          {step === 2 && renderStep2()}
          {step === 3 && renderStep3()}
        </CardContent>
      </Card>
    </div>
  );
};

export default Onboarding;
