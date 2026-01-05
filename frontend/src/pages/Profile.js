import React, { useState, useEffect, useContext } from 'react';
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
import { ArrowLeft, User, MapPin, Compass, FileText, Clock, AlertCircle } from 'lucide-react';

const RADIUS_OPTIONS = [3, 5, 10];

export const Profile = () => {
  const [displayName, setDisplayName] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [locationStatus, setLocationStatus] = useState(null);
  const [showLocationDialog, setShowLocationDialog] = useState(false);
  const [showRadiusDialog, setShowRadiusDialog] = useState(false);
  const [newZone, setNewZone] = useState('');
  const [selectedRadius, setSelectedRadius] = useState(5);
  const [updatingLocation, setUpdatingLocation] = useState(false);
  const [updatingRadius, setUpdatingRadius] = useState(false);
  const [termsStatus, setTermsStatus] = useState(null);
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { user, login } = useContext(AuthContext);

  useEffect(() => {
    fetchProfile();
    fetchLocationStatus();
    fetchTermsStatus();
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
      const response = await api.get('/user/location-status');
      setLocationStatus(response.data);
      setSelectedRadius(response.data.radius?.km || 5);
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
    if (!newZone.trim()) {
      toast.error(t('profile.enterZone'));
      return;
    }
    
    setUpdatingLocation(true);
    try {
      // For now, use approximate coordinates based on zone name
      // In production, this would use a geocoding service
      await api.put('/user/location', {
        zone: newZone.trim(),
        lat: -34.6037 + (Math.random() - 0.5) * 0.1, // Buenos Aires area
        lng: -58.3816 + (Math.random() - 0.5) * 0.1
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
      await api.put('/user/radius', {
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
            {/* Location Zone */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>{t('profile.zone')}</Label>
                {locationStatus?.location?.can_change ? (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowLocationDialog(true)}
                  >
                    {locationStatus?.location?.zone ? t('profile.changeLocation') : t('profile.setLocation')}
                  </Button>
                ) : (
                  <Badge variant="secondary" className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {t('profile.cooldown', { days: locationStatus?.location?.days_until_change || 0 })}
                  </Badge>
                )}
              </div>
              <div className="bg-muted rounded-lg p-3">
                {locationStatus?.location?.zone ? (
                  <p className="font-medium">{locationStatus.location.zone}</p>
                ) : (
                  <p className="text-muted-foreground italic">{t('profile.noLocationSet')}</p>
                )}
              </div>
            </div>

            {/* Search Radius */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>{t('profile.searchRadius')}</Label>
                {locationStatus?.radius?.can_change ? (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowRadiusDialog(true)}
                  >
                    {t('profile.changeRadius')}
                  </Button>
                ) : (
                  <Badge variant="secondary" className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {t('profile.cooldown', { days: locationStatus?.radius?.days_until_change || 0 })}
                  </Badge>
                )}
              </div>
              <div className="bg-muted rounded-lg p-3">
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

        {/* Location Change Dialog */}
        <Dialog open={showLocationDialog} onOpenChange={setShowLocationDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{t('profile.changeLocation')}</DialogTitle>
              <DialogDescription>
                {t('profile.changeLocationDescription')}
              </DialogDescription>
            </DialogHeader>
            <div className="py-4">
              <Label htmlFor="zone">{t('profile.zone')}</Label>
              <Input
                id="zone"
                placeholder={t('profile.zonePlaceholder')}
                value={newZone}
                onChange={(e) => setNewZone(e.target.value)}
              />
              <p className="text-xs text-muted-foreground mt-2">
                {t('profile.zoneHelp')}
              </p>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowLocationDialog(false)}>
                {t('common.cancel')}
              </Button>
              <Button onClick={handleUpdateLocation} disabled={updatingLocation}>
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
