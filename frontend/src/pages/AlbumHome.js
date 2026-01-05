import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Users, Package, UserPlus, ExternalLink, Settings, LogOut } from 'lucide-react';
import { Progress } from '@/components/ui/progress';

const maskEmail = (email) => {
  if (!email) return '';
  const [local, domain] = email.split('@');
  if (local.length <= 3) {
    return `${local[0]}***@${domain}`;
  }
  return `${local.substring(0, 3)}***@${domain}`;
};

const getDisplayName = (user, t) => {
  if (!user) return t('app.defaultUser');
  
  // Priority 1: Display name if exists
  if (user.display_name && user.display_name.trim()) {
    return user.display_name.trim();
  }
  
  // Priority 2: Masked email
  if (user.email) {
    return maskEmail(user.email);
  }
  
  return t('app.defaultUser');
};

export const AlbumHome = () => {
  const { albumId } = useParams();
  const [album, setAlbum] = useState(null);
  const [loading, setLoading] = useState(true);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [membersDialogOpen, setMembersDialogOpen] = useState(false);
  const [deactivateDialogOpen, setDeactivateDialogOpen] = useState(false);
  const [deactivating, setDeactivating] = useState(false);
  const [inviteLink, setInviteLink] = useState('');
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    fetchAlbum();
  }, [albumId]);

  const fetchAlbum = async () => {
    try {
      const response = await api.get(`/albums/${albumId}`);
      setAlbum(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
      navigate('/albums');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateInvite = async () => {
    try {
      const response = await api.post(`/albums/${albumId}/invites`);
      const link = `${window.location.origin}/join/${response.data.token}`;
      setInviteLink(link);
      toast.success(t('invite.generate'));
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    }
  };

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(inviteLink);
      toast.success(t('invite.copied'));
    } catch (error) {
      console.log('Clipboard API not available, user can select manually');
    }
  };

  const handleSelectLink = () => {
    const input = document.getElementById('invite-link-input');
    if (input) {
      input.select();
    }
  };

  const handleOpenInNewTab = () => {
    window.open(inviteLink, '_blank');
  };

  const handleDeactivateAlbum = async () => {
    setDeactivating(true);
    try {
      await api.delete(`/albums/${albumId}/deactivate`);
      toast.success(t('albums.deactivateSuccess'));
      setDeactivateDialogOpen(false);
      navigate('/albums');
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setDeactivating(false);
    }
  };

  // Exchange count from backend (mutual matches only)
  const exchangeCount = album?.exchange_count ?? 0;

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
        <div className="flex items-center gap-4 mb-8">
          <Button
            data-testid="back-to-albums-btn"
            variant="outline"
            size="icon"
            onClick={() => navigate('/albums')}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex-1">
            <h1 className="text-3xl font-black tracking-tight text-primary">{album?.name}</h1>
            <p className="text-muted-foreground">{album?.year} • {album?.category}</p>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                data-testid="album-settings-btn"
                variant="outline"
                size="icon"
              >
                <Settings className="h-5 w-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem 
                data-testid="deactivate-album-menu-item"
                onClick={() => setDeactivateDialogOpen(true)}
                className="text-destructive cursor-pointer"
              >
                <LogOut className="h-4 w-4 mr-2" />
                {t('albums.deactivate')}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {album?.has_placeholder && (
          <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <p className="text-sm text-amber-900">
              {t('albumHome.placeholderBanner')}
            </p>
          </div>
        )}

        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold">{t('albumHome.progress')}</span>
            <span className="text-sm font-bold text-primary">{Math.round(album?.progress ?? 0)}%</span>
          </div>
          <Progress value={Math.round(album?.progress ?? 0)} className="h-3" />
        </div>

        {/* Exchange Status Panel - Core value proposition */}
        <Card 
          data-testid="exchange-status-card" 
          className={`mb-6 ${exchangeCount > 0 ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}
        >
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className={`h-10 w-10 rounded-full flex items-center justify-center ${
                exchangeCount > 0 ? 'bg-green-100' : 'bg-gray-100'
              }`}>
                <Package className={`h-5 w-5 ${exchangeCount > 0 ? 'text-green-600' : 'text-gray-400'}`} />
              </div>
              <div>
                {exchangeCount > 0 ? (
                  <p className="font-semibold text-green-800">
                    {t('albumHome.exchangesAvailable', { count: exchangeCount })}
                  </p>
                ) : (
                  <p className="font-medium text-gray-600">
                    {t('albumHome.noExchangesAvailable')}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <Card
            data-testid="inventory-card"
            className="hover:shadow-lg transition-all cursor-pointer border-2 hover:border-primary"
            onClick={() => navigate(`/albums/${albumId}/inventory`)}
          >
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                {t('albumHome.myInventory')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {t('albumHome.manageInventory')}
              </p>
            </CardContent>
          </Card>

          <Card
            data-testid="matches-card"
            className="hover:shadow-lg transition-all cursor-pointer border-2 hover:border-primary"
            onClick={() => navigate(`/albums/${albumId}/matches`)}
          >
            <CardHeader>
              <CardTitle>{t('albumHome.exchanges')}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {t('albumHome.findExchanges')}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Invite button removed - exchanges happen organically through matches */}

        {/* Deactivate Album Dialog */}
        <Dialog open={deactivateDialogOpen} onOpenChange={setDeactivateDialogOpen}>
          <DialogContent data-testid="deactivate-dialog">
            <DialogHeader>
              <DialogTitle>{t('albums.deactivate')}</DialogTitle>
              <DialogDescription>
                {t('albums.deactivateQuestion')}
              </DialogDescription>
            </DialogHeader>
            <DialogFooter className="gap-2 sm:gap-0">
              <Button
                data-testid="cancel-deactivate-btn"
                variant="outline"
                onClick={() => setDeactivateDialogOpen(false)}
                disabled={deactivating}
              >
                {t('common.cancel')}
              </Button>
              <Button
                data-testid="confirm-deactivate-btn"
                variant="destructive"
                onClick={handleDeactivateAlbum}
                disabled={deactivating}
              >
                {deactivating ? t('common.loading') : t('albums.deactivateConfirm')}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default AlbumHome;
