import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Settings, BookOpen, Plus, Users } from 'lucide-react';

// Helper to get translated album name from nameKey
const getAlbumNameDisplay = (album, t) => {
  if (album?.name_key) {
    return t(`albumNames.${album.name_key}`);
  }
  return album?.name || '';
};

// Helper to get translated category from categoryKey
const getCategoryDisplay = (album, t) => {
  if (album?.category_key) {
    return t(`categories.${album.category_key}`);
  }
  return album?.category || '';
};

export const Groups = () => {
  const [groups, setGroups] = useState([]);
  const [albums, setAlbums] = useState([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [selectedAlbum, setSelectedAlbum] = useState(null);
  const [groupName, setGroupName] = useState('');
  const [creating, setCreating] = useState(false);
  const [joinDialogOpen, setJoinDialogOpen] = useState(false);
  const [inviteCode, setInviteCode] = useState('');
  const [joining, setJoining] = useState(false);
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [groupsRes, albumsRes] = await Promise.all([
        api.get('/groups'),
        api.get('/albums')
      ]);
      setGroups(groupsRes.data);
      setAlbums(albumsRes.data.filter(a => a.status === 'active'));
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGroup = async () => {
    if (!selectedAlbum || !groupName.trim()) return;
    
    setCreating(true);
    try {
      const response = await api.post('/groups', {
        album_id: selectedAlbum.id,
        name: groupName.trim()
      });
      toast.success(t('groups.createSuccess'));
      setCreateDialogOpen(false);
      setGroupName('');
      setSelectedAlbum(null);
      navigate(`/groups/${response.data.group.id}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setCreating(false);
    }
  };

  const handleJoinGroup = async () => {
    if (!inviteCode.trim() || inviteCode.length !== 6) return;
    
    setJoining(true);
    try {
      const response = await api.post('/invites/accept', {
        invite_code: inviteCode.trim()
      });
      toast.success(t('groups.joinSuccess'));
      setJoinDialogOpen(false);
      setInviteCode('');
      fetchData();
      navigate(`/groups/${response.data.group_id}`);
    } catch (error) {
      const detail = error.response?.data?.detail;
      if (detail === 'INVITE_EXPIRED') {
        toast.error(t('groups.inviteExpired'));
      } else {
        toast.error(detail || t('common.error'));
      }
    } finally {
      setJoining(false);
    }
  };

  const getMemberCountDisplay = (count) => {
    if (count === 0) return `0 ${t('groups.memberPlural')}`;
    if (count === 1) return `1 ${t('groups.member')}`;
    return `${count} ${t('groups.memberPlural')}`;
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
            <h1 className="text-3xl font-black tracking-tight text-primary">{t('groups.title')}</h1>
            <p className="text-muted-foreground">{t('groups.subtitle')}</p>
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

        {/* Action buttons */}
        <div className="grid grid-cols-2 gap-4 mb-8">
          <Button
            data-testid="create-group-btn"
            onClick={() => setCreateDialogOpen(true)}
            className="h-16 btn-primary"
          >
            <Plus className="h-5 w-5 mr-2" />
            {t('groups.create')}
          </Button>
          <Button
            data-testid="join-group-btn"
            variant="outline"
            onClick={() => setJoinDialogOpen(true)}
            className="h-16"
          >
            <Users className="h-5 w-5 mr-2" />
            {t('groups.joinWithCode')}
          </Button>
        </div>

        {/* Groups list */}
        {groups.length === 0 ? (
          <div className="text-center py-16 text-muted-foreground">
            <BookOpen className="h-16 w-16 mx-auto mb-4 opacity-50" />
            <p className="text-lg">{t('groups.noGroups')}</p>
            <p className="text-sm mt-2">{t('groups.noGroupsHint')}</p>
          </div>
        ) : (
          <div className="space-y-4">
            {groups.map((group) => (
              <Card
                key={group.id}
                data-testid={`group-item-${group.id}`}
                className="cursor-pointer transition-all hover:shadow-lg border-2 hover:border-primary"
                onClick={() => navigate(`/groups/${group.id}`)}
              >
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="h-16 w-16 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
                        <BookOpen className="h-8 w-8 text-primary" />
                      </div>
                      <div>
                        <h3 className="text-xl font-bold">{group.name}</h3>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <span>{getAlbumNameDisplay(group.album, t)}</span>
                          <span>•</span>
                          <span>{getMemberCountDisplay(group.member_count)}</span>
                          <span>•</span>
                          <span className="font-semibold text-primary">
                            {group.progress}% {t('groups.completed')}
                          </span>
                        </div>
                      </div>
                    </div>
                    {group.is_owner && (
                      <Badge className="bg-amber-100 text-amber-700">{t('groups.owner')}</Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Create Group Dialog */}
        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogContent data-testid="create-group-dialog">
            <DialogHeader>
              <DialogTitle>{t('groups.createTitle')}</DialogTitle>
              <DialogDescription>{t('groups.createDescription')}</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <label className="text-sm font-medium mb-2 block">{t('groups.selectAlbum')}</label>
                <div className="grid grid-cols-1 gap-2 max-h-48 overflow-y-auto">
                  {albums.map((album) => (
                    <div
                      key={album.id}
                      data-testid={`album-option-${album.id}`}
                      className={`p-3 border rounded-lg cursor-pointer transition-all ${
                        selectedAlbum?.id === album.id
                          ? 'border-primary bg-primary/5'
                          : 'hover:border-gray-300'
                      }`}
                      onClick={() => setSelectedAlbum(album)}
                    >
                      <p className="font-medium">{getAlbumNameDisplay(album, t)}</p>
                      <p className="text-sm text-muted-foreground">{album.year} • {getCategoryDisplay(album, t)}</p>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">{t('groups.groupName')}</label>
                <Input
                  data-testid="group-name-input"
                  placeholder={t('groups.groupNamePlaceholder')}
                  value={groupName}
                  onChange={(e) => setGroupName(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setCreateDialogOpen(false)}
                disabled={creating}
              >
                {t('common.cancel')}
              </Button>
              <Button
                data-testid="confirm-create-btn"
                onClick={handleCreateGroup}
                disabled={creating || !selectedAlbum || !groupName.trim()}
                className="btn-primary"
              >
                {creating ? t('common.loading') : t('groups.create')}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Join Group Dialog */}
        <Dialog open={joinDialogOpen} onOpenChange={setJoinDialogOpen}>
          <DialogContent data-testid="join-group-dialog">
            <DialogHeader>
              <DialogTitle>{t('groups.joinTitle')}</DialogTitle>
              <DialogDescription>{t('groups.joinDescription')}</DialogDescription>
            </DialogHeader>
            <div className="py-4">
              <label className="text-sm font-medium mb-2 block">{t('groups.enterCode')}</label>
              <Input
                data-testid="invite-code-input"
                placeholder="000000"
                value={inviteCode}
                onChange={(e) => setInviteCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                maxLength={6}
                className="text-center text-2xl tracking-widest"
              />
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setJoinDialogOpen(false)}
                disabled={joining}
              >
                {t('common.cancel')}
              </Button>
              <Button
                data-testid="confirm-join-btn"
                onClick={handleJoinGroup}
                disabled={joining || inviteCode.length !== 6}
                className="btn-primary"
              >
                {joining ? t('common.loading') : t('groups.join')}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default Groups;
