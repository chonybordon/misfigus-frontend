import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Settings, BookOpen, CheckCircle } from 'lucide-react';
import { PaywallModal } from '../components/Paywall';

// Helper to get translated category name from categoryKey
const getCategoryDisplay = (album, t) => {
  // If album has categoryKey, use i18n translation
  if (album.category_key) {
    return t(`categories.${album.category_key}`);
  }
  // Fallback to raw category (for backward compat with old data)
  return album.category;
};

// Helper to get translated album name from nameKey
const getAlbumNameDisplay = (album, t) => {
  // If album has nameKey, use i18n translation
  if (album.name_key) {
    return t(`albumNames.${album.name_key}`);
  }
  // Fallback to raw name (for backward compat with old data)
  return album.name;
};

export const Albums = () => {
  const [albums, setAlbums] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAlbum, setSelectedAlbum] = useState(null);
  const [activationDialogOpen, setActivationDialogOpen] = useState(false);
  const [activating, setActivating] = useState(false);
  const [paywallOpen, setPaywallOpen] = useState(false);
  const [paywallReason, setPaywallReason] = useState(null);
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    fetchAlbums();
  }, []);

  const fetchAlbums = async () => {
    try {
      const response = await api.get('/albums');
      setAlbums(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const handleAlbumClick = (album) => {
    // COMING_SOON: Not clickable
    if (album.user_state === 'coming_soon') {
      return; // Do nothing - not clickable
    }
    
    // INACTIVE: Can activate
    if (album.user_state === 'inactive') {
      setSelectedAlbum(album);
      setActivationDialogOpen(true);
      return;
    }
    
    // ACTIVE: Navigate to album
    navigate(`/albums/${album.id}`);
  };

  const handleActivateAlbum = async () => {
    if (!selectedAlbum) return;
    
    setActivating(true);
    try {
      await api.post(`/albums/${selectedAlbum.id}/activate`);
      toast.success(t('albums.activateSuccess'));
      setActivationDialogOpen(false);
      navigate(`/albums/${selectedAlbum.id}`);
    } catch (error) {
      // Check for freemium limit error
      const errorDetail = error.response?.data?.detail;
      if (errorDetail?.code === 'ALBUM_LIMIT') {
        setActivationDialogOpen(false);
        setPaywallReason('ALBUM_LIMIT');
        setPaywallOpen(true);
      } else {
        toast.error(typeof errorDetail === 'string' ? errorDetail : t('common.error'));
      }
    } finally {
      setActivating(false);
    }
  };

  const handlePaywallUpgrade = () => {
    // Refresh albums to reflect premium status
    fetchAlbums();
    // Try activating again
    if (selectedAlbum) {
      handleActivateAlbum();
    }
  };

  // VISUAL STATE BADGES
  const getStateBadge = (album) => {
    if (album.user_state === 'coming_soon') {
      // COMING_SOON: Gray badge (unchanged)
      return (
        <Badge 
          variant="secondary" 
          className="bg-gray-200 text-gray-600 px-3 py-1 text-xs font-semibold"
        >
          {t('albums.comingSoonBadge')}
        </Badge>
      );
    }
    if (album.user_state === 'inactive') {
      // INACTIVE: RED pill badge with WHITE text
      return (
        <Badge 
          className="bg-red-500 text-white px-3 py-1 text-xs font-semibold hover:bg-red-500"
        >
          {t('albums.inactiveBadge')}
        </Badge>
      );
    }
    // ACTIVE: Green pill badge (unchanged)
    return (
      <Badge 
        className="bg-green-500 text-white px-3 py-1 text-xs font-semibold hover:bg-green-500"
      >
        {t('albums.activeBadge')}
      </Badge>
    );
  };

  // Get card styles based on state
  const getCardStyles = (album) => {
    if (album.user_state === 'coming_soon') {
      // COMING_SOON: Gray, not clickable
      return 'opacity-50 cursor-not-allowed';
    }
    if (album.user_state === 'inactive') {
      // INACTIVE: Gray text, clickable
      return 'cursor-pointer hover:shadow-lg hover:border-orange-300';
    }
    // ACTIVE: Normal, clickable
    return 'cursor-pointer hover:shadow-lg hover:border-primary';
  };

  // Get title text color based on state
  const getTitleStyles = (album) => {
    if (album.user_state === 'coming_soon' || album.user_state === 'inactive') {
      return 'text-gray-500'; // GRAY for inactive/coming_soon
    }
    return 'text-foreground'; // Normal color for active
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-2xl font-bold">{t('common.loading')}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen sticker-album-pattern overflow-x-hidden">
      <div className="w-full max-w-4xl mx-auto px-4 sm:px-6 py-4 sm:py-6">
        <div className="flex items-center justify-between gap-3 mb-6 sm:mb-8">
          <div className="min-w-0 flex-1">
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-primary truncate">{t('albums.title')}</h1>
            <p className="text-sm sm:text-base text-muted-foreground">{t('albums.subtitle')}</p>
          </div>
          <Button
            data-testid="settings-btn"
            variant="outline"
            size="icon"
            onClick={() => navigate('/settings')}
            className="flex-shrink-0"
          >
            <Settings className="h-5 w-5" />
          </Button>
        </div>

        <div className="space-y-3 sm:space-y-4">
          {albums.map((album) => (
            <Card
              key={album.id}
              data-testid={`album-item-${album.id}`}
              className={`transition-all border-2 ${getCardStyles(album)}`}
              onClick={() => handleAlbumClick(album)}
            >
              <CardContent className="p-4 sm:p-6">
                <div className="flex items-start sm:items-center justify-between gap-3">
                  <div className="flex items-start sm:items-center gap-3 sm:gap-4 min-w-0 flex-1">
                    <div className={`h-12 w-12 sm:h-16 sm:w-16 rounded-xl flex items-center justify-center flex-shrink-0 ${
                      album.user_state === 'coming_soon' || album.user_state === 'inactive'
                        ? 'bg-gray-100'
                        : 'bg-gradient-to-br from-primary/20 to-primary/5'
                    }`}>
                      <BookOpen className={`h-6 w-6 sm:h-8 sm:w-8 ${
                        album.user_state === 'coming_soon' || album.user_state === 'inactive'
                          ? 'text-gray-400'
                          : 'text-primary'
                      }`} />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className={`text-base sm:text-xl font-bold truncate ${getTitleStyles(album)}`}>{getAlbumNameDisplay(album, t)}</h3>
                        {/* Completion checkmark for 100% completed albums */}
                        {album.is_member && album.progress === 100 && (
                          <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-green-700 flex-shrink-0" />
                        )}
                      </div>
                      <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs sm:text-sm text-muted-foreground">
                        <span>{album.year}</span>
                        <span className="hidden sm:inline">•</span>
                        <span>{getCategoryDisplay(album, t)}</span>
                        {/* Show progress for active albums */}
                        {album.is_member && album.progress !== undefined && (
                          <>
                            <span className="hidden sm:inline">•</span>
                            <span className={`font-semibold ${
                              album.progress === 100 
                                ? 'text-green-700' 
                                : 'text-primary'
                            }`}>
                              {Math.round(album.progress)}%
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    {getStateBadge(album)}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Activation Dialog */}
        <Dialog open={activationDialogOpen} onOpenChange={setActivationDialogOpen}>
          <DialogContent data-testid="activation-dialog">
            <DialogHeader>
              <DialogTitle>{t('albums.activateTitle')}</DialogTitle>
              <DialogDescription>
                {t('albums.activateQuestion')}
              </DialogDescription>
            </DialogHeader>
            <div className="py-4">
              <p className="font-semibold text-lg">{selectedAlbum?.name}</p>
              <p className="text-sm text-muted-foreground">
                {selectedAlbum?.year} • {selectedAlbum && getCategoryDisplay(selectedAlbum, t)}
              </p>
            </div>
            <DialogFooter className="gap-2 sm:gap-0">
              <Button
                data-testid="cancel-activate-btn"
                variant="outline"
                onClick={() => setActivationDialogOpen(false)}
                disabled={activating}
              >
                {t('common.cancel')}
              </Button>
              <Button
                data-testid="confirm-activate-btn"
                onClick={handleActivateAlbum}
                disabled={activating}
                className="btn-primary"
              >
                {activating ? t('common.loading') : t('albums.activate')}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Paywall Modal */}
        <PaywallModal
          isOpen={paywallOpen}
          onClose={() => setPaywallOpen(false)}
          reason={paywallReason}
          onUpgradeSuccess={handlePaywallUpgrade}
        />
      </div>
    </div>
  );
};

export default Albums;
