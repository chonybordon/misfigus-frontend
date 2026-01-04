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
    if (album.user_state === 'coming_soon') {
      toast.info(t('albums.comingSoon'));
      return;
    }
    
    if (album.user_state === 'inactive') {
      setSelectedAlbum(album);
      setActivationDialogOpen(true);
      return;
    }
    
    // Active album - navigate to it
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

  const getStateBadge = (album) => {
    if (album.user_state === 'coming_soon') {
      return <Badge variant="secondary" className="bg-gray-100 text-gray-600">{t('albums.comingSoonBadge')}</Badge>;
    }
    if (album.user_state === 'inactive') {
      return <Badge variant="outline" className="border-orange-300 text-orange-600">{t('albums.inactiveBadge')}</Badge>;
    }
    return <Badge className="bg-green-100 text-green-700">{t('albums.activeBadge')}</Badge>;
  };

  // Helper for consistent member count display
  const getMemberCountDisplay = (album) => {
    const count = album.member_count ?? 0;
    if (count === 0) return `0 ${t('albumHome.memberPlural')}`;
    if (count === 1) return `1 ${t('albumHome.member')}`;
    return `${count} ${t('albumHome.memberPlural')}`;
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
              className={`cursor-pointer transition-all hover:shadow-lg border-2 ${
                album.user_state === 'coming_soon' 
                  ? 'opacity-60 hover:border-gray-300' 
                  : album.user_state === 'active'
                    ? 'hover:border-primary'
                    : 'hover:border-orange-300'
              }`}
              onClick={() => handleAlbumClick(album)}
            >
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="h-16 w-16 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
                      <BookOpen className="h-8 w-8 text-primary" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold">{album.name}</h3>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span>{album.year}</span>
                        <span>•</span>
                        <span>{album.category}</span>
                        {/* SINGLE SOURCE: Use member_count from backend (already excludes current user) */}
                        {album.is_member && album.member_count !== undefined && (
                          <>
                            <span>•</span>
                            <span>{getMemberCountDisplay(album)}</span>
                          </>
                        )}
                        {album.is_member && album.progress !== undefined && (
                          <>
                            <span>•</span>
                            <span className="font-semibold text-primary">
                              {album.progress}% {t('albumHome.completed')}
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
