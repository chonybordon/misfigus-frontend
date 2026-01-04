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

  // SINGLE SOURCE OF TRUTH: Use member_count from backend directly
  // Backend EXCLUDES owner from this count - owner is NEVER a member
  const memberCount = album?.member_count ?? 0;

  // Get member count display string with proper singular/plural
  const getMemberCountDisplay = () => {
    if (memberCount === 0) {
      return `0 ${t('albumHome.memberPlural')}`;
    } else if (memberCount === 1) {
      return `1 ${t('albumHome.member')}`;
    } else {
      return `${memberCount} ${t('albumHome.memberPlural')}`;
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
            <p className="text-muted-foreground">
              {getMemberCountDisplay()}
            </p>
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

        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold">{t('albumHome.progress')}</span>
            <span className="text-sm font-bold text-primary">{album?.progress ?? 0}%</span>
          </div>
          <Progress value={album?.progress ?? 0} className="h-3" />
        </div>

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
              <CardTitle>{t('albumHome.matches')}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {t('albumHome.findTrades')}
              </p>
            </CardContent>
          </Card>
        </div>

        <Card data-testid="members-card" className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                {t('albumHome.members')}
              </div>
              {memberCount > 0 && (
                <Button
                  data-testid="view-all-members-btn"
                  variant="outline"
                  size="sm"
                  onClick={() => setMembersDialogOpen(true)}
                >
                  {t('members.viewAll')}
                </Button>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {/* EMPTY STATE: 0 members (owner is NEVER a member) */}
            {memberCount === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <p>{t('albumHome.noOtherMembers')}</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {/* SINGLE SOURCE: Use album.members from backend (excludes owner) */}
                {album?.members?.slice(0, 6).map((member) => (
                  <div key={member.id} className="flex items-center gap-2 p-2 rounded-lg bg-muted">
                    <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold text-sm">
                      {getDisplayName(member, t)[0].toUpperCase()}
                    </div>
                    <span className="text-sm font-medium truncate">{getDisplayName(member, t)}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Dialog open={inviteDialogOpen} onOpenChange={setInviteDialogOpen}>
          <DialogTrigger asChild>
            <Button
              data-testid="invite-member-btn"
              className="w-full btn-secondary"
            >
              <UserPlus className="h-5 w-5 mr-2" />
              {t('albumHome.invite')}
            </Button>
          </DialogTrigger>
          <DialogContent data-testid="invite-dialog">
            <DialogHeader>
              <DialogTitle>{t('invite.title')}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">{t('invite.subtitle')}</p>
              
              {!inviteLink ? (
                <Button
                  data-testid="generate-invite-btn"
                  onClick={handleGenerateInvite}
                  className="w-full btn-primary"
                >
                  {t('invite.generate')}
                </Button>
              ) : (
                <div className="space-y-3">
                  <div>
                    <input
                      id="invite-link-input"
                      data-testid="invite-link-input"
                      type="text"
                      value={inviteLink}
                      readOnly
                      className="w-full p-3 border rounded-lg text-sm bg-muted font-mono"
                    />
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <Button
                      data-testid="copy-invite-btn"
                      onClick={handleCopyLink}
                      variant="outline"
                      size="sm"
                    >
                      {t('invite.copy')}
                    </Button>
                    <Button
                      data-testid="select-invite-btn"
                      onClick={handleSelectLink}
                      variant="outline"
                      size="sm"
                    >
                      {t('invite.select')}
                    </Button>
                    <Button
                      data-testid="open-invite-btn"
                      onClick={handleOpenInNewTab}
                      variant="outline"
                      size="sm"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </div>
                  <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs space-y-1">
                    <p>• {t('invite.expires')}</p>
                    <p>• {t('invite.singleUse')}</p>
                  </div>
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>

        {/* Members Modal - Uses album.members from backend (excludes owner) */}
        <Dialog open={membersDialogOpen} onOpenChange={setMembersDialogOpen}>
          <DialogContent data-testid="members-dialog" className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>{t('members.title')}</DialogTitle>
            </DialogHeader>
            <div className="max-h-[60vh] overflow-y-auto">
              <div className="space-y-2">
                {album?.members?.map((member) => (
                  <div key={member.id} className="flex items-center justify-between p-3 rounded-lg bg-muted">
                    <div className="flex items-center gap-3 flex-1">
                      <div className="h-10 w-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                        {getDisplayName(member, t)[0].toUpperCase()}
                      </div>
                      <div className="flex-1">
                        <p className="font-semibold">{getDisplayName(member, t)}</p>
                        <p className="text-xs text-muted-foreground">{maskEmail(member.email)}</p>
                      </div>
                    </div>
                    <Badge variant="secondary">
                      {t('members.member')}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          </DialogContent>
        </Dialog>

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
