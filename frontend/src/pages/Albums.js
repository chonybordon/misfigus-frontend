import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api, AuthContext } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Settings as SettingsIcon, ChevronRight } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';

export const Albums = () => {
  const [albums, setAlbums] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activationDialogOpen, setActivationDialogOpen] = useState(false);
  const [selectedAlbum, setSelectedAlbum] = useState(null);
  const [activating, setActivating] = useState(false);
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { user } = useContext(AuthContext);

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
      return;
    }
    
    if (album.user_state === 'active') {
      navigate(`/albums/${album.id}`);
    } else if (album.user_state === 'inactive') {
      setSelectedAlbum(album);
      setActivationDialogOpen(true);
    }
  };

  const handleActivateAlbum = async () => {
    if (!selectedAlbum) return;
    
    setActivating(true);
    try {
      await api.post(`/albums/${selectedAlbum.id}/activate`);
      toast.success(t('albums.activateSuccess'));
      setActivationDialogOpen(false);
      fetchAlbums(); // Refresh albums list
      navigate(`/albums/${selectedAlbum.id}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || t('albums.activateError'));
    } finally {
      setActivating(false);
    }
  };

  const getAlbumBadge = (userState) => {
    if (userState === 'active') {
      return (
        <Badge className="bg-green-500 text-white">
          {t('albums.active')}
        </Badge>
      );
    } else if (userState === 'inactive') {
      return (
        <Badge variant="secondary" className="bg-gray-400 text-white">
          {t('albums.inactive')}
        </Badge>
      );
    } else {
      return (
        <Badge variant="secondary" className="bg-gray-400 text-white">
          {t('albums.comingSoon')}
        </Badge>
      );
    }
  };

  const getAlbumStyles = (userState) => {
    if (userState === 'active') {
      return 'hover:shadow-md cursor-pointer border-2 hover:border-primary';
    } else if (userState === 'inactive') {
      return 'hover:shadow-md cursor-pointer border-2 border-dashed opacity-75 hover:opacity-100';
    } else {
      return 'opacity-50 cursor-not-allowed border-2 border-dashed';
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
      <div className="max-w-4xl mx-auto p-6">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-black tracking-tight text-primary mb-1">
              {t('app.name')}
            </h1>
            <p className="text-muted-foreground">{user?.email}</p>
          </div>
          <Button
            data-testid="settings-btn"
            variant="outline"
            size="icon"
            onClick={() => navigate('/settings')}
          >
            <SettingsIcon className="h-5 w-5" />
          </Button>
        </div>

        <h2 className="text-2xl font-bold mb-4">{t('albums.select')}</h2>

        {albums.length === 0 ? (
          <div className="text-center py-20" data-testid="no-albums-message">
            <p className="text-muted-foreground">{t('albums.noAlbums')}</p>
          </div>
        ) : (
          <div className="space-y-2" data-testid="albums-list">
            {albums.map((album) => (
              <div
                key={album.id}
                data-testid={`album-item-${album.id}`}
                className={`bg-white rounded-lg p-4 flex items-center justify-between transition-all ${getAlbumStyles(album.user_state)}`}
                onClick={() => handleAlbumClick(album)}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="text-lg font-bold">{album.name}</h3>
                    {getAlbumBadge(album.user_state)}
                  </div>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span>{album.year}</span>
                    <span>•</span>
                    <span>{album.category}</span>
                    {album.is_member && album.member_count && (
                      <>
                        <span>•</span>
                        <span>{album.member_count} {t('albumHome.members')}</span>
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
                {album.user_state === 'active' && (
                  <ChevronRight className="h-5 w-5 text-muted-foreground" />
                )}
              </div>
            ))}
          </div>
        )}

        <Dialog open={activationDialogOpen} onOpenChange={setActivationDialogOpen}>
          <DialogContent data-testid="activation-dialog">
            <DialogHeader>
              <DialogTitle>{t('albums.activate')}</DialogTitle>
            </DialogHeader>
            <div className="py-4">
              <p className="text-lg mb-4">{t('albums.activateQuestion')}</p>
              {selectedAlbum && (
                <div className="bg-muted p-4 rounded-lg">
                  <p className="font-bold text-lg">{selectedAlbum.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {selectedAlbum.year} • {selectedAlbum.category}
                  </p>
                </div>
              )}
            </div>
            <DialogFooter>
              <Button
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
                {activating ? t('common.loading') : t('albums.activateConfirm')}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default Albums;
