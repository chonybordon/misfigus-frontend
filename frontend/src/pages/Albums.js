import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Settings, BookOpen } from 'lucide-react';

export const Albums = () => {
  const [albums, setAlbums] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAlbum, setSelectedAlbum] = useState(null);
  const [activationDialogOpen, setActivationDialogOpen] = useState(false);
  const [activating, setActivating] = useState(false);
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
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setActivating(false);
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
    <div className="min-h-screen sticker-album-pattern">
      <div className="max-w-4xl mx-auto p-6">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-black tracking-tight text-primary">{t('albums.title')}</h1>
            <p className="text-muted-foreground">{t('albums.subtitle')}</p>
          </div>
          <Button
            data-testid="settings-btn"
            variant="outline"
            size="icon"
            onClick={() => navigate('/settings')}
          >
            <Settings className="h-5 w-5" />
          </Button>
        </div>

        <div className="space-y-4">
          {albums.map((album) => (
            <Card
              key={album.id}
              data-testid={`album-item-${album.id}`}
              className={`transition-all border-2 ${getCardStyles(album)}`}
              onClick={() => handleAlbumClick(album)}
            >
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`h-16 w-16 rounded-xl flex items-center justify-center ${
                      album.user_state === 'coming_soon' || album.user_state === 'inactive'
                        ? 'bg-gray-100'
                        : 'bg-gradient-to-br from-primary/20 to-primary/5'
                    }`}>
                      <BookOpen className={`h-8 w-8 ${
                        album.user_state === 'coming_soon' || album.user_state === 'inactive'
                          ? 'text-gray-400'
                          : 'text-primary'
                      }`} />
                    </div>
                    <div>
                      <h3 className={`text-xl font-bold ${getTitleStyles(album)}`}>{album.name}</h3>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span>{album.year}</span>
                        <span>•</span>
                        <span>{album.category}</span>
                        {/* Show progress for active albums */}
                        {album.is_member && album.progress !== undefined && (
                          <>
                            <span>•</span>
                            <span className="font-semibold text-primary">
                              {Math.round(album.progress)}% {t('albumHome.completed')}
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  {getStateBadge(album)}
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
                {selectedAlbum?.year} • {selectedAlbum?.category}
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
      </div>
    </div>
  );
};

export default Albums;
