import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api, AuthContext } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Settings as SettingsIcon, ChevronRight } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export const Albums = () => {
  const [albums, setAlbums] = useState([]);
  const [loading, setLoading] = useState(true);
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
    if (album.status === 'coming_soon') {
      return;
    }
    
    if (album.is_member) {
      navigate(`/albums/${album.id}`);
    } else {
      // For ACTIVE albums, join directly without invitation
      joinAlbum(album.id);
    }
  };

  const joinAlbum = async (albumId) => {
    try {
      await api.post(`/albums/${albumId}/join`);
      toast.success('Te has unido al álbum');
      fetchAlbums(); // Refresh to update membership status
      navigate(`/albums/${albumId}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
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
                className={`bg-white rounded-lg p-4 flex items-center justify-between transition-all ${
                  album.status === 'coming_soon'
                    ? 'opacity-50 cursor-not-allowed'
                    : album.is_member
                    ? 'hover:shadow-md cursor-pointer border-2 hover:border-primary'
                    : 'cursor-not-allowed border-2 border-dashed'
                }`}
                onClick={() => handleAlbumClick(album)}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="text-lg font-bold">{album.name}</h3>
                    <Badge
                      variant={album.status === 'active' ? 'default' : 'secondary'}
                      className={album.status === 'active' ? 'bg-green-500' : 'bg-gray-400'}
                    >
                      {album.status === 'active' ? t('albums.active') : t('albums.comingSoon')}
                    </Badge>
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
                {album.is_member && album.status === 'active' && (
                  <ChevronRight className="h-5 w-5 text-muted-foreground" />
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Albums;
